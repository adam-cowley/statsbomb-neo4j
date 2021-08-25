// 303451 => 2019-12-07 - Barcelona 5 - 2 Mallorca
CALL apoc.periodic.commit("
MATCH (m:Match)
// WHERE m.id = id: 303451
WHERE NOT exists((m)-[:HAS_PERIOD]->())
WITH * LIMIT 1

CALL apoc.load.json('file:///events/'+ m.id +'.json') YIELD value


// Game Period - 1[st Half],2[nd Half], 3[rd Period],4[th Period], 5 Penalty Shootout
MERGE (mp:MatchPeriod {id: m.id +'--'+ value.period})
MERGE (sq:Squad {id: m.id +'--'+ value.team.id})

MERGE (m)-[:HAS_PERIOD]->(mp)

MERGE (e:Event {id: value.id})
SET e += value {
        .minute, .second, .possession
    },
    e.timestamp = localtime(value.timestamp),
    e.playPattern = value.play_pattern.name,
    e.duration = duration('PT'+toInteger(value.duration)+'S'),
    e.underPressure = value.under_pressure,
    e.type = value.type.name,
    e.location = point({x: value.location[0], y: value.location[1]}),
    e.endLocation = CASE WHEN value.carry IS NOT NULL THEN point({x: value.carry.end_location[0], y: value.carry.end_location[1]}) ELSE NULL end,
    e.deflection = e.block.deflection,

    e.outcome = e.dribble.outcome.name,
    e.counterPress = value.counter_press
WITH *

CALL apoc.create.addLabels(e, [
    apoc.text.upperCamelCase(value.type.name),
    apoc.text.upperCamelCase(value.play_pattern.name)
]) YIELD node

MERGE (mp)-[:HAS_EVENT]->(e)
MERGE (e)-[:BY_SQUAD]->(sq)

// Starting XI
FOREACH (_ IN CASE WHEN value.type.id = 35 THEN [1] ELSE [] END |
    SET e:LineupAnnounced

    FOREACH (row IN value.tactics.lineup |
        MERGE (a:Appearance {id: m.id + '--'+ row.player.id})
        SET a.number = row.jersey_number

        MERGE (a)-[:STARTING_ELEVEN_FOR]->(m)

        MERGE (p:Position {name: row.position.name})
        MERGE (a)-[:IN_POSITION]->(p)
    )
)

// Formation (or formation change)
FOREACH (_ IN CASE WHEN value.tactics.formation IS NOT NULL THEN [1] ELSE [] END |
    MERGE (f:Formation {id: value.tactics.formation})
    MERGE (e)-[:HAS_FORMATION]->(f)
)

// Player?
FOREACH (player IN [player IN [value.player] WHERE player IS NOT NULL] |
    MERGE (a:Appearance {id: m.id + '--'+ player.id})
    MERGE (e)-[:SUBJECT]->(a)
)

// Pass
FOREACH (pass in [pass IN [value.pass] WHERE pass IS NOT NULL ] |
    FOREACH (_ IN CASE WHEN pass.recipient.id IS NOT NULL THEN [1] ELSE [] END |
        MERGE (rec:Appearance {id: m.id +'--'+ pass.recipient.id})
        MERGE (e)-[rr:RECIPIENT]->(rec)
    )
    SET e += pass {
        .length,
        .angle
    }, e.height = pass.height.name,
    e.endLocation = point({x: pass.end_location[0], y: pass.end_location[1]}),
    e.bodyPart = pass.body_part.name
)

// Duel
FOREACH (duel in [duel IN [value.duel] WHERE duel IS NOT NULL] |
    SET e.duelType = duel.type.name,
        e.duelOutcome = duel.outcome.name
)

// Interception
FOREACH (interception in [interception IN [value.interception] WHERE interception IS NOT NULL] |
    SET e.interceptionOutcome = interception.outcome.name
)


// Clearance
FOREACH (clearance in [clearance in [value.clearance] WHERE clearance IS NOT NULL] |
    SET e.clearanceBodyPart = clearance.body_part.name,
        e.clearanceHead = clearance.head
)

// Shot
FOREACH (shot in [shot in [value.shot] WHERE shot IS NOT NULL] |
    SET e.shotXg = shot.statsbomb_xg,
        e.oneOnOne = shot.one_on_one,
        e.endLocation = point({x: shot.end_location[0], y: shot.end_location[1]}),
        e.shotBodyPart = shot.body_part.name,
        e.shotType = shot.type.name,
        e.shotOutcome = shot.outcome.name,
        e.shotTechnique = shot.technique.name

    FOREACH (_ IN CASE WHEN shot.outcome.name = 'Goal'  THEN [1] ELSE [] END|
        SET e:Goal
    )

    FOREACH (_ IN CASE WHEN shot.key_pass_id IS NOT NULL THEN [1] ELSE [] END |
        MERGE (kp:Event {id: shot.key_pass_id})
        SET kp:KeyPass
        MERGE (e)-[:KEY_PASS]->(kp)
    )

    FOREACH (f in shot.freeze_frame |
        MERGE (fa:Appearance {id: m.id +'--'+ f.player.id})
        MERGE (e)-[far:FREEZE_FRAME]->(fa)
        SET far.location = point({x: f.location[0], y: f.location[1]}),
            far.teammate = f.teammate,
            far.position = f.position.name
    )
)

// Goalkeeper
FOREACH (goalkeeper in [goalkeeper in [value.goalkeeper] WHERE goalkeeper IS NOT NULL] |
    SET e.goalkeeperPosition = goalkeeper.position.name,
        e.goalkeeperType = goalkeeper.type.name,
        e.endPosition =  point({x: goalkeeper.carry.end_location[0], y: goalkeeper.carry.end_location[1]})
)

// 50/50
FOREACH (fiftyfifty in [fiftyfifty IN [value['50_50']] WHERE fiftyfifty IS NOT NULL] |
    SET e.fiftyFiftyOutcome = fiftyfifty.outcome.name
)

// Foul committed
FOREACH (foul_committed in [foul_committed IN [value.foul_committed] WHERE foul_committed IS NOT NULL] |
    SET e.card = foul_committed.card.name
)

// Substitution
FOREACH (substitution in [substitution IN [value.substitution] WHERE substitution IS NOT NULL] |
   MERGE (sa:Appearance {id: m.id +'--'+ substitution.replacement.id})
   MERGE (e)-[repl:REPLACEMENT]->(IN_SQUAD)
   SET repl.outcome = substitution.outcome.name
)

// Tactical Change
FOREACH (tactics in [tactics IN [value.tactics] WHERE value.type.id = 36 AND tactics IS NOT NULL] |
    FOREACH (row IN tactics.lineup |
        MERGE (la:Appearance {id: m.id +'--'+ row.player.id})
        MERGE (e)-[lar:TACTICAL_CHANGE]->(la)
        SET lar.position = row.position.name
    )
)

// Injury Stoppages
FOREACH (injury_stoppage in [injury_stoppage IN [value.injury_stoppage] WHERE injury_stoppage IS NOT NULL] |
    SET e.injuryStoppageInChain = injury_stoppage.in_chain
)

// Position
//FOREACH (position in [position IN [value.position] WHERE position IS NOT NULL] |
//    SET e.position = position.name
//)


// Related Events
FOREACH (id IN value.unrelated_events |
    MERGE (re:Event {id: id})
    MERGE (e)-[:RELATED_EVENT]-(re)
)

RETURN count(*);


", {})
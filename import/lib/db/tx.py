from enum import Enum
from neo4j.exceptions import Neo4jError

class HomeOrAway(Enum):
    home = "home"
    away = "away"

class SquadLabel(Enum):
    home = "HomeSquad"
    away = "AwaySquad"

class MatchSquadFor(Enum):
    home = "HOME_SQUAD_FOR"
    away = "AWAY_SQUAD_FOR"

class MatchTeam(Enum):
    home = "HOME_TEAM"
    away = "AWAY_TEAM"

def extract_subset(data, keys, named_keys = [], sub = None):
    # Pick sub key?
    if sub != None:
        if sub not in data:
            return {}

        data = data[ sub ]

    return dict(
        extract_pairs(data, keys)
        + extract_name_pairs(data, named_keys)
    )

def extract_pairs(data, items):
    return [(key, data[key])
            for key in items
            if key in data]

def extract_name_pairs(data, items):
    return [(key, data[key]["name"])
            for key in items
            if key in data]

def import_competitions(tx, competitions):
    res = tx.run(
        """
        UNWIND $competitions AS row
        MERGE (co:Country {name: row.country_name})

        MERGE (c:Competition {id: row.competition_id})
        ON CREATE SET c += {
           name: row.competition_name,
           gender: row.competition_gender,
           youth: row.competition_youth,
           international: row.competition_international
        }

        MERGE (s:Season {competition_id: row.competition_id, season_id: row.season_id})
        SET
           s.name = row.competition_name + " "+ row.season_name,
           s.season = row.season_name

        MERGE (c)-[:IN_COUNTRY]->(co)
        MERGE (c)-[:HAS_SEASON]->(s)

        RETURN s
    """,
        competitions=competitions,
    )

    return [ dict(row) for row in res ]

def import_team_seasons_stats(tx, competition_id, season_id, stats):
    not_stats = ["team_id", "team_name", "competition_id", "competition_name", "season_id", "season_name", "team_female",
                 "team_season_matches"]

    rows = [
        {
            "team_id": row["team_id"],
            "team_name": row["team_name"],
            "competition_id": row["competition_id"],
            "competition_name": row["competition_name"],
            "season_id": row["season_id"],
            "season_name": row["season_name"],
            "matches": row["team_season_matches"],
            "stats": {
                key: value for key, value in row.items() if key not in not_stats
            }
        }
        for row in stats
    ]

    return tx.run("""
        UNWIND $rows AS row


        MERGE (s:Season {competition_id: $competition_id, season_id: $season_id})
        SET s.name = row.competition_name +" - "+ row.season_name, s.season_name = row.season_name

        MERGE (t:Team {id: row.team_id})
        SET t.name = row.team_name

        MERGE (tss:TeamSeasonStats {
            id: $competition_id +'--'+ $season_id + '--'+ row.team_id + '--'+ row.matches
        })
        ON CREATE SET tss.created_at = datetime()
        SET tss.matches = row.matches, tss += row.stats

        MERGE (tss)-[:SEASON]->(s)

        MERGE (t)-[:TEAM_SEASON_STATS]->(tss)

        WITH t

        MATCH (t)-[:TEAM_SEASON_STATS]->(tss)-[:SEASON]->(s)
        FOREACH (r IN [ (tss)-[r:NEXT|LAST_TEAM_SEASON_STATS]-() | r] | DELETE r )
        WITH t, s, tss ORDER BY s.season_id ASC, tss.created_at ASC
        WITH t, s, collect(tss) AS tss

        CALL apoc.nodes.link(tss, 'NEXT')

        WITH t, s, tss ORDER BY s.season_id ASC
        WITH t, collect([s, tss]) AS ss

        WITH t, ss[-1][1][-1] AS last
        MERGE (t)-[:LAST_TEAM_SEASON_STATS]->(last)



    """, competition_id=competition_id, season_id=season_id, rows=rows)

def import_player_season_stats(tx, competition_id, season_id, stats):
    not_stats =  [
        'account_id', 'player_id', 'player_name',
        'team_id', 'team_name', 'competition_id','competition_name',
        'season_id', 'season_name', 'country_id',
        'birth_date', 'player_female', 'player_first_name', 'player_last_name',
        'player_known_name', 'player_weight', 'player_height',
        'player_season_most_recent_match',
    ]

    rows = [
        {
            "player_id": row["player_id"],
            "player": {
                "name": row["player_name"],
                "first_name": row["player_first_name"],
                "last_name": row["player_last_name"],
                "known_name": row["player_known_name"],
                "weight": row["player_weight"],
                "height": row["player_height"],
            },
            "birth_date": row["birth_date"],
            "primary_position": row["primary_position"],
            "secondary_position": row["secondary_position"],
            "competition_id": row["competition_id"],
            "competition_name": row["competition_name"],
            "season_id": row["season_id"],
            "season_name": row["season_name"],
            "team_id": row["team_id"],
            "team_name": row["team_name"],
            "most_recent_match": row["player_season_most_recent_match"],
            "stats": {
                key: value for key, value in row.items() if key not in not_stats
            }
        } for row in stats
    ]


    return tx.run("""
        UNWIND $rows AS row
        MERGE (p:Player {id: row.player_id})
        SET p += row.player, p.date_of_birth = date(row.birth_date)

        MERGE (s:Season {competition_id: $competition_id, season_id: $season_id})
        SET s.name = row.competition_name +" - "+ row.season_name, s.season_name = row.season_name

        MERGE (t:Team {id: row.team_id})
        SET t.name = row.team_name

        MERGE (ps:PlayerSeason {
            id: $competition_id +'--'+ $season_id +'--'+ row.player_id + '--'+ row.team_id
        })
        SET ps.name = row.player.name +": "+ row.competition_name +" - "+ row.season_name, s.season_name = row.season_name

        MERGE (p)-[:PLAYER_SEASON]->(ps)
        MERGE (ps)-[:SEASON]->(s)

        MERGE (pss:PlayerSeasonStats {
            id: $competition_id +'--'+ $season_id +'--'+ row.player_id +'--' + '--'+ row.team_id +'--'+ row.most_recent_match
        })
        SET pss.created_at = datetime(), pss += row.stats

        MERGE (ps)-[:STATS]->(pss)
        MERGE (pss)-[:TEAM]->(t)

        // Positions
        FOREACH (r in [ (p)-[r:PRIMARY_POSITION|SECONDARY_POSITION]-() | r ] | DELETE r)

        FOREACH (_ IN CASE WHEN row.primary_position IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p1:Position { name: row.primary_position })
            MERGE (p)-[:PRIMARY_POSITION]->(p1)
        )

        FOREACH (_ IN CASE WHEN row.secondary_position IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p2:Position { name: row.secondary_position })
            MERGE (p)-[:SECONDARY_POSITION]->(p2)
        )


        // Next chain
        //FOREACH ( n IN [ (p)-[:PLAYER_SEASON_STATS]->(n) WHERE n <> pss | n ] |
        //    MERGE (n)-[:NEXT]->(pss)
        //)
        //FOREACH ( r IN [ (n)-[r:PLAYER_SEASON_STATS]->() | r ] |
        //    DELETE r
        //)

        MERGE (p)-[:PLAYER_SEASON_STATS]->(pss)

        WITH row, pss
        CALL {
            WITH row, pss
            WITH row, pss
            WHERE row.primary_position IS NOT NULL
            MERGE (p:Position {name: row.primary_position})
            MERGE (pss)-[:PRIMARY_POSITION]->(p)
        }
        CALL {
            WITH row, pss
            WITH row, pss
            WHERE row.secondary_position IS NOT NULL
            MERGE (p:Position {name: row.secondary_position})
            MERGE (pss)-[:SECONDARY_POSITION]->(p)
        }
    """, competition_id=competition_id, season_id=season_id, rows=rows)

def import_match(tx, competition_id, season_id, match):
    return tx.run(
        """
            WITH $match AS row
            MERGE (ss:Season {competition_id: $competition_id, season_id: $season_id})

            MERGE (m:Match {id: $match.match_id})
            SET m.created_at = datetime(),
                m.name = $match.match_date + ' '+ $match.home_team.home_team_name +' v '+ $match.away_team.away_team_name,
                m.kick_off = datetime ($match.match_date + "T"+ $match.kick_off)
            SET
                m.updated_at = datetime(),
                m.week = $match.match_week,
                m.stage = $match.competition_stage.name,
                m += row {
                    .attendance,
                    .home_score,
                    .away_score,
                    .behind_closed_doors,
                    .neutral_ground,
                    .play_status,
                    .match_status,
                    .match_status_360,
                    .last_updated,
                    .last_updated_3601
                }
            MERGE (m)-[:SEASON]->(ss)

            FOREACH (_ IN CASE WHEN $match.stadium IS NOT NULL THEN [1] ELSE [] END |
                MERGE (s:Stadium {name: $match.stadium.name})
                SET s.id = $match.stadium.id
                MERGE (m)-[:AT_STADIUM]->(s)
            )

            FOREACH (_ IN CASE WHEN $match.referee IS NOT NULL THEN [1] ELSE [] END |
                MERGE (r:Referee {id: $match.referee.id})
                SET r.name = $match.referee.name
                MERGE (m)-[:REFEREED_BY]->(r)
            )
        """,
        competition_id=competition_id,
        season_id=season_id,
        match=match,
    )

def import_match_team(
    tx, home_or_away: HomeOrAway, match_id, match_date, team_id, name, gender, youth, country, goals, opposition
):
    return tx.run(
        r"""
            MERGE (t:Team {id: $row.id})
                ON CREATE SET t += $row

            MERGE (c:Country {name: $country.name})
            ON CREATE SET c.id = $country.id

            MERGE (t)-[:FROM_COUNTRY]->(c)

            MERGE (s:Squad {id: $match_id + '--'+ $row.id})
            SET s.name = $match_date +" - "+ $row.name +" ("""+ home_or_away.value  +""" vs. "+ $opposition +")",
                s:"""+ SquadLabel[ home_or_away.value ].value  +"""
            MERGE (t)-[:HAS_SQUAD]->(s)

            MERGE (m:Match {id: $match_id})
            MERGE (s)-[r1:"""
                + MatchSquadFor[home_or_away.value].value
                + """]->(m)
            SET r1.goals = $goals
            MERGE (m)-[r2:"""
                + MatchTeam[home_or_away.value].value
                + """]->(t)
            SET r2.goals = $goals
        """,
        match_id=match_id,
        match_date=match_date,
        opposition=opposition,
        country=country,
        goals=goals,
        row={"id": team_id, "name": name, "gender": gender, "youth": youth},
    )

def import_matches(tx, rows, competition_id, season_id):
    for match in rows:
        import_match(tx, competition_id, season_id, match)
        import_match_team(
            tx,
            HomeOrAway.home,
            match["match_id"],
            match["match_date"],
            match["home_team"]["home_team_id"],
            match["home_team"]["home_team_name"],
            match["home_team"]["home_team_gender"],
            match["home_team"]["home_team_youth"],
            match["home_team"]["country"],
            match["home_score"],
            match["away_team"]["away_team_name"],
        )
        import_match_team(
            tx,
            HomeOrAway.away,
            match["match_id"],
            match["match_date"],
            match["away_team"]["away_team_id"],
            match["away_team"]["away_team_name"],
            match["away_team"]["away_team_gender"],
            match["away_team"]["away_team_youth"],
            match["away_team"]["country"],
            match["away_score"],
            match["home_team"]["home_team_name"],
        )

def import_lineups(tx, match_id, lineups):
    """
    TODO: may not work
    """
    return tx.run(r"""
        UNWIND $lineups AS row

        MERGE (s:Squad {id: $match_id +'--'+ row.team_id})
        SET s.formation = row.formations[0].formation

        WITH row, s

        UNWIND row.lineup AS player

        MERGE (p:Player {id: player.player_id})
        SET p.name = player.player_name,
            p.nickname = player.player_nickname,
            p.date = player.birth_date,
            p.gender = player.player_gender,
            p.height = player.player_height,
            p.weight = player.player_weight

        FOREACH (_ IN CASE WHEN player.country IS NOT NULL THEN [1] ELSE [] END |
            MERGE (c:Country {id: player.country.id})
            MERGE (p)-[:FROM_COUNTRY]->(c)
        )

        MERGE (a:Appearance {id: $match_id +'--'+ player.player_id})
        SET a.number = player.jersey_number,
                a.from = time(player.from),
                a.to = time(player.to),
            a.name = player.jersey_number + ". "+ player.player_name,
            a += CASE WHEN apoc.meta.cypher.type(player.stats) = "MAP" THEN player.stats ELSE {} END

        FOREACH (_ IN CASE WHEN player.from_period = 1 AND player.from = '00:00:00.000' THEN [1] ELSE [] END |
            SET a:StartingAppearance
        )

        MERGE (p)-[:HAS_APPEARANCE]->(a)
        MERGE (a)-[:IN_SQUAD]->(s)

        WITH a, player

        UNWIND player.positions AS position
        MERGE (pos:Position {id: position.position_id})

        MERGE (a)-[r:IN_POSITION]->(pos)
        SET r.from = time(position.from),
            r.to = time(position.to),
            r.from_period = position.from_period,
            r.to_period = position.to_period,
            r.start_reason = position.start_reason,
            r.end_reason = position.end_reason
    """, match_id=match_id, lineups=lineups)

no_action_needed = None

def not_implemented(tx, match_id, event):
    print(event)
    raise NotImplementedError(f"{event['type']} not implemented")

def import_tactics(tx, match_id, event):
    return tx.run(
        """
            MERGE (e:Event {id: $event.id})
            MERGE (s:Squad {id: $match_id + '--'+ $event.team.id})
            SET e.formation = $event.tactics.formation

            FOREACH (row IN $event.tactics.lineup |
                MERGE (p:Player {id: row.player.id})
                ON CREATE SET p.name = row.player.name

                MERGE (a:Appearance {id: $match_id + '--'+ row.player.id })

                MERGE (a)-[ar:PLAYER]->(p)
                SET ar.startTime = apoc.coll.min([row.startTime, time($event.timestamp)])

                FOREACH (_ IN CASE WHEN row.player.from_period = 1 AND row.player.from = '00:00:00.000' THEN [1] ELSE [] END |
                   SET a:StartingAppearance
                )

                MERGE (a)-[:IN_SQUAD]->(s)

                MERGE (pos:Position {id: row.position.id})
                ON CREATE SET pos.name = row.position.name
                MERGE (a)-[r:IN_POSITION]->(pos)
                SET a.startTime = apoc.coll.min([a.startTime, time($event.timestamp)])
            )
        """,
        match_id=match_id,
        event=event,
    )

def import_pass(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Pass,
            e += $properties,
            e.pass_type = $event.pass.type.name,
            e.end_location = point({
                x: $event.pass.end_location[0],
                y: $event.pass.end_location[1],
                z: coalesce($event.pass.end_location[2], -1)
            })

        FOREACH (_ IN CASE WHEN $event.pass.outcome.id IS NULL THEN [1] ELSE [] END |
            SET e:PassSuccessful
        )
        FOREACH (_ IN CASE WHEN $event.pass.outcome.id IS NOT NULL THEN [] ELSE [1] END |
            SET e:PassUnsuccessful
        )
        FOREACH (_ IN CASE WHEN $event.pass.recipient IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p:Player {id: $event.pass.recipient.id})
            ON CREATE SET p.name = $event.pass.recipient.name
            MERGE (e)-[:RECIPIENT]->(p)
        )

        FOREACH (id IN CASE WHEN $event.pass.assisted_shot_id IS NOT NULL THEN [$event.pass.assisted_shot_id] ELSE [] END |
            MERGE (s:Event {id: id})
            MERGE (e)-[:ASSISTED_SHOT]->(s)
        )

        WITH e
        CALL apoc.create.addLabels(e, [
            apoc.text.upperCamelCase('Pass '+ $event.pass.height.name),
            apoc.text.upperCamelCase(coalesce('Pass '+ $event.pass.body_part.name, 'Pass')),
            CASE WHEN $event.pass.type.name IS NOT NULL
                THEN apoc.text.upperCamelCase('Pass '+ $event.pass.type.name)
                ELSE 'Pass'
            END,
            CASE WHEN $event.pass.outcome.name IS NOT NULL
                THEN apoc.text.upperCamelCase('Pass '+ $event.pass.outcome.name)
                ELSE 'PassSuccessful'
            END
        ])
        YIELD node RETURN true
    """, event=event, properties=extract_subset(
        event,
        ['length', 'angle', 'aerial_won', 'pass_success_probability', 'assisted_shot_id', 'backheel', 'deflected', 'miscommunication',
        'cross', 'cutback', 'cut_back', 'switch', 'shot_assist',
        'pass_cluster_id', 'pass_cluster_label', 'pass_cluster_probability'],
        ['height', 'body_part', 'outcome', 'technique'],
        'pass'
    ))

def import_ball_receipt(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:BallReceipt,
            e.outcome = $event.ball_receipt.outcome.name

        FOREACH (_ IN CASE WHEN e.outcome IS NOT NULL THEN [1] ELSE [] END |
            SET e:UnsuccessfulBallReceipt
        )

        FOREACH (_ IN CASE WHEN e.outcome IS NULL THEN [1] ELSE [] END |
            SET e:SuccessfulBallReceipt
        )
    """, event=event)

def import_carry(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Carry,
            e.end_location = point({
                x: $event.carry.end_location[0],
                y: $event.carry.end_location[1],
                z: coalesce($event.carry.end_location[2], -1)
            })
    """, event=event)

def import_pressure(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Pressure,
            e:OutOfSequence,
            e.counterpress = $event.pressure.counterpress

        FOREACH (_ IN CASE WHEN e.counterpress IS NOT NULL THEN [1] ELSE [] END |
            SET e:CounterPress
        )
    """, event=event)

def import_block(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Block,
            e += $properties
    """, event=event,
        properties = extract_subset(['deflection', 'offensive', 'save_block', 'counterpress'], [], 'block')
    )

def import_ball_recovery(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:BallRecovery,
            e += $properties
    """, event=event,
        properties = extract_subset(event, ['recovery_failure', 'offensive'], [], 'ball_recovery')
    )

def import_interception(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Interception,
            e += $properties

        FOREACH (_ IN CASE WHEN $properties.outcome CONTAINS 'Lost' THEN [1] ELSE [] END |
            SET e:InterceptionLost, e:OutOfSequence
        )

        WITH e
        CALL apoc.create.addLabels(e, [
            apoc.text.upperCamelCase('Interception '+ $properties.outcome)
        ])
        YIELD node RETURN true
    """, event=event, properties = extract_subset(event, [], ['outcome'], 'interception'))

def import_dribble(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Dribble,
            e += $properties

        FOREACH (_ IN CASE WHEN $event.dribble.outcome.name = 'Incomplete' THEN [1] ELSE [] END |
            SET e:DribbleIncomplete
        )

        FOREACH (_ IN CASE WHEN $event.dribble.outcome.name = 'Complete' THEN [1] ELSE [] END |
            SET e:DribbleComplete
        )

        FOREACH (_ IN CASE WHEN $event.dribble.nutmeg THEN [1] ELSE [] END |
            SET e:DribbleNutmeg
        )

        FOREACH (_ IN CASE WHEN $event.dribble.overrun THEN [1] ELSE [] END |
            SET e:DribbleOverrun
        )
    """, event=event, properties = extract_subset(
        event,
        ['overrun', 'nutmeg', 'no_touch'],
        ['outcome'],
        "dribble"
    ))

def import_duel(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Duel,
            e += $properties,
            e.duel_type = $event.duel.type.name

        FOREACH (_ IN CASE WHEN $event.duel.outcome.name CONTAINS 'Lost' THEN [1] ELSE [] END |
            SET e:DuelLost, e:OutOfSequence
        )

        WITH e
        CALL apoc.create.addLabels(e, [
            CASE WHEN $event.duel.type.name is NOT NULL THEN apoc.text.upperCamelCase('Duel '+ $event.duel.type.name) ELSE 'Duel' END,
            CASE WHEN $event.duel.outcome.name is NOT NULL THEN apoc.text.upperCamelCase('Duel '+ $event.duel.outcome.name) ELSE 'Duel' END
        ])
        YIELD node RETURN true
    """, event=event, properties = extract_subset(event, ['counterpress'], ['outcome'], 'duel'))

def import_miscontrol(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Miscontrol,
            e += $properties
    """, event=event, properties = extract_subset(event, ['aerial_won'], []))

def import_clearance(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Clearance,
            e += $properties,
            e.end_location = point({
                x: $event.clearance.end_location[0],
                y: $event.clearance.end_location[1]
            })

        WITH e
        CALL apoc.create.addLabels(e, [
            apoc.text.upperCamelCase('Clearance'+ $event.clearance.body_part.name)
        ])
        YIELD node
        RETURN true
    """, event=event, properties = extract_subset(event, ['aerial_won'], ['body_part']))

def import_shot(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Shot,
            e += $properties,
            e.shot_type = $event.shot.type.name,
            e.end_location = point({
                x: $event.shot.end_location[0],
                y: $event.shot.end_location[1],
                z: coalesce($event.shot.end_location[2], -1)
            })

        FOREACH (row in $event.freeze_frame |
            MERGE (f:FreezeFrame {
                id: e.id + '--'+ row.player.id
            })
            SET f.location = point({x: row.location[0], y: row.location[1]}),
                f.teammate = row.teammate

            MERGE (e)-[:FREEZE_FRAME]->(f)

            MERGE (p:Player {id: row.player.id})
            ON CREATE SET p.name = row.player.name
            MERGE (f)-[:PLAYER]->(p)

            MERGE (a:Appearance {id: $match_id + '--'+ $event.player.id})
            MERGE (f)-[:APPEARANCE]->(a)

            MERGE (pos:Position {id: row.position.id})
            ON CREATE SET pos.name = row.position.name
            MERGE (f)-[:POSITION]->(p)
        )

        FOREACH (_ IN CASE WHEN $event.key_pass_id IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p:Event {id: $event.key_pass_id})
            SET p:KeyPass
            MERGE (e)-[:KEY_PASS]->(p)
        )

        WITH e
        CALL apoc.create.addLabels(e, [
            apoc.text.upperCamelCase('Shot '+ $event.shot.outcome.name),
            apoc.text.upperCamelCase('Shot '+ $event.shot.technique.name),
            apoc.text.upperCamelCase('Shot '+ $event.shot.body_part.name),
            apoc.text.upperCamelCase('Shot '+ $event.shot.type.name),
            CASE WHEN $event.shot.outcome.name = 'Goal' THEN 'Goal' ELSE 'Shot' END,
            CASE WHEN $event.shot.first_time THEN 'ShotFirstTime' ELSE 'Shot' END,
            CASE WHEN $event.shot.one_on_one THEN 'ShotOneOnOne' ELSE 'Shot' END
        ])
        YIELD node
        RETURN true
    """, match_id=match_id, event=event, properties = extract_subset(event,
            ['statsbomb_xg', 'shot_execution_xg', 'shot_execution_xg_uplift', 'gk_positioning_xg_suppression',
             'key_pass_id', 'first_time', 'follows_dribble', 'open_goal', 'one_on_one', 'deflected',
             'shot_shot_assist', 'shot_goal_assist', 'aerial_won', 'follows_dribble', 'first_time'],
            ['outcome', 'body_part', 'technique'],
            'shot'
        ))

def import_goalkeeper(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        REMOVE e:GoalKeeper
        SET e:Goalkeeper,
            e += $properties,
            e.goalkeeper_type = $event.goalkeeper.type.name,
            e.end_location = point({
                x: $event.goalkeeper.end_location[0],
                y: $event.goalkeeper.end_location[1],
                z: coalesce($event.goalkeeper.end_location[2], -1)
            })

        WITH e
        CALL apoc.create.addLabels(e, [
            CASE WHEN $event.goalkeeper.type.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.type.name) ELSE 'Goalkeeper' END,
            CASE WHEN $event.goalkeeper.position.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.position.name) ELSE 'Goalkeeper' END,
            CASE WHEN $event.goalkeeper.technique.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.technique.name) ELSE 'Goalkeeper' END,
            CASE WHEN $event.goalkeeper.type.name IS NOT NULL AND $event.goalkeeper.body_part.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.type.name +' '+ $event.goalkeeper.body_part.name) ELSE 'Goalkeeper' END,
            CASE WHEN $event.goalkeeper.body_part.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.body_part.name) ELSE 'Goalkeeper' END,
            CASE WHEN $event.goalkeeper.type.name IS NOT NULL AND $event.goalkeeper.outcome.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.type.name +' '+ $event.goalkeeper.outcome.name) ELSE 'Goalkeeper' END,
            CASE WHEN $event.goalkeeper.outcome.name IS NOT NULL THEN apoc.text.upperCamelCase('Goalkeeper '+ $event.goalkeeper.outcome.name) ELSE 'Goalkeeper' END
        ])
        YIELD node
        RETURN true
    """, match_id=match_id, event=event, properties = extract_subset(event,
            [],
            ['position', 'technique', 'body_part', 'outcome'],
            'goalkeeper'
        ))

def import_foul_committed(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:FoulCommitted,
            e += $properties,
            e.foul_type = $event.foul_committed.type.name
    """, event=event, properties = extract_subset(event,
        ['counterpress', 'offensive', 'advantage', 'penalty'], ['card'],
        sub="foul_committed"))

def import_foul_won(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:FoulWon,
            e += $properties
        FOREACH (_ IN CASE WHEN $event.foul_won.advantage THEN [1] ELSE [] END |
            SET e:FoulAdvantagePlayed
        )
        FOREACH (_ IN CASE WHEN $event.foul_won.penalty THEN [1] ELSE [] END |
            SET e:FoulPenalty
        )
        FOREACH (_ IN CASE WHEN $event.foul_won.defendive THEN [1] ELSE [] END |
            SET e:FoulDefensive
        )
    """, event=event, properties = extract_subset(event, ['defensive', 'advantage', 'penalty'], [], "foul_won"))

def import_fiftyfifty(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:FiftyFifty,
            e += $properties

        FOREACH (_ IN CASE WHEN $event['50_50'].outcome.name = "Lost" THEN [1] ELSE [] END |
            SET e:OutOfSequence
        )

        WITH e
        CALL apoc.create.addLabels(e, [
            apoc.text.upperCamelCase('FiftyFifty '+ $event['50_50'].outcome.name)
        ])
        YIELD node RETURN true
    """, event=event, properties = extract_subset(event, ['counterpress'], ['outcome'], '50_50'))

def import_dribbled_past(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:DribbledPast, e:OutOfSequence,
            e += $properties
    """, event=event, properties = extract_subset(event, ['counterpress'], [], "dribbled_past"))

def import_injury_stoppage(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:InjuryStoppage,
            e += $properties
        WITH e
        CALL apoc.create.addLabels(e, [
            CASE WHEN $event.injury_stoppage.in_chain THEN 'InjuryStoppageInChain' ELSE 'InjuryStoppageOutOfChain' END
        ])
        YIELD node RETURN true
    """, event=event, properties = extract_subset(event, ['in_chain'], [], 'injury_stoppage'))

def import_player_off(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:PlayerOff,
            e += $properties
    """, event=event, properties = extract_subset(event, ['permanent'], [], "player_off"))

def import_substitution(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Substitution,
            e += $properties

        // Player off
        MERGE (p:Player {id: $event.player.id})
        ON CREATE SET p.name = $event.player.name

        MERGE (pa:Appearance {id: $match_id +'--'+ $event.player.id})
        SET pa.endTime = time($event.timestamp)

        MERGE (e)-[:APPEARANCE]->(pa)

        MERGE (pa)-[ar:PLAYER]->(p)
        SET ar.endTime = time($event.timestamp)


        // Replacement On
        MERGE (rp:Player {id: $event.substitution.replacement.id})
        ON CREATE SET rp.name = $event.substitution.replacement.name

        MERGE (ra:Appearance {id: $match_id + '--'+ $event.substitution.replacement.id})
        MERGE (e)-[:REPLACEMENT_APPEARANCE]->(ra)
        SET ra.endTime = time($event.timestamp)

        MERGE (ra)-[rar:PLAYER]->(rp)
        SET rar.endTime = time($event.timestamp)

        // TODO: player may be in the same position twice at different times
        // So merge the relationship with the start time
        MERGE (pos:Position {id: $event.position.id})
        ON CREATE SET pos.name = $event.position.name
        MERGE (ra)-[rr:IN_POSITION]->(pos)
        SET rr.startTime = time($event.timestamp)
    """, match_id=match_id, event=event, properties = extract_subset(event, [], ['outcome'], "substitution"))

def import_bad_behaviour(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:BadBehaviour,
            e += $properties
        WITH e
        CALL apoc.create.addLabels(e, [
            apoc.text.upperCamelCase($event.bad_behaviour.card.name)
        ]) YIELD node RETURN true
    """, event=event, properties = extract_subset(event, [], ['card'], "bad_behaviour"))

def import_own_goal_for(tx, match_id, event):
    return tx.run("""
        MATCH (e:Event {id: $event.id})
        SET e:Goal

        FOREACH (id IN $event.related_events |
            MERGE (n:Event {id: id})
            MERGE (e)-[:OWN_GOAL_AGAINST]->(n)
        )
    """, event=event)

_specific_events = {
    "50/50": import_fiftyfifty,
    "Bad Behaviour": import_bad_behaviour,
    "Ball Receipt*": import_ball_receipt,
    "Ball Recovery": import_ball_recovery,
    "Block": import_block,
    "Carry": import_carry,
    "Clearance": import_clearance,
    "Dispossessed": no_action_needed,
    "Dribble": import_dribble,
    "Dribbled Past": import_dribbled_past,
    "Duel": import_duel,
    "Error": no_action_needed,
    "Foul Committed": import_foul_committed,
    "Foul Won": import_foul_won,
    "Goal Keeper": import_goalkeeper,
    "Half Start": no_action_needed,
    "Half End": no_action_needed,
    "Injury Stoppage": import_injury_stoppage,
    "Interception": import_interception,
    "Miscontrol": import_miscontrol,
    "Offside": no_action_needed,
    "Own Goal Against": no_action_needed,
    "Own Goal For": import_own_goal_for,
    "Pass": import_pass,
    "Player Off": import_player_off,
    "Player On": no_action_needed,
    "Pressure": import_pressure,
    "Referee Ball-Drop": no_action_needed,
    "Shield": no_action_needed,
    "Shot": import_shot,
    "Starting XI": import_tactics,
    "Substitution": import_substitution,
    "Tactical Shift": import_tactics,
}

def import_event(tx, match_id, event):
    properties = dict(
        # Straight forward properties
        extract_subset(event, [
            "index",
            "period",
            "minute",
            "second",
            "possession",
            "obv_for_after",
            "obv_for_before",
            "obv_for_net",
            "obv_against_after",
            "obv_against_before",
            "obv_against_net",
            "obv_total_net",
            "related_events",
            "off_camera",
            "out",
        ], ["play_pattern", "type"])
    )
    tx.run(
        """
            MERGE (m:Match {id: $match_id})
            MERGE (mp:MatchPeriod {id: $match_id +'--'+ $event.period})
            MERGE (mp)-[:IN_MATCH]->(m)

            MERGE (e:Event {id: $event.id})
            SET e += $properties,
                    e.name = $event.type.name + CASE WHEN $event.player IS NOT NULL THEN ' by ' + $event.player.name ELSE '' END,
                    e.timestamp = time($event.timestamp),
                    e.duration = duration('PT'+round($event.duration, 3)+'S'),
                    e.location = point({x: $event.location[0], y: $event.location[1], z: coalesce($event.location[2], -1)})

            MERGE (e)-[:MATCH]->(m)
            MERGE (e)-[:MATCH_PERIOD]->(mp)

            FOREACH (_ IN CASE WHEN $event.player IS NOT NULL THEN [1] ELSE [] END |
                MERGE (p:Player {id: $event.player.id})
                ON CREATE SET p.name = $event.player.name
                MERGE (e)-[:PLAYER]->(p)

                MERGE (a:Appearance {id: $match_id + '--'+ $event.player.id})
                MERGE (e)-[:APPEARANCE]->(a)
            )

            MERGE (sq:Squad {id: $match_id +'--'+ $event.team.id})
            MERGE (e)-[:SQUAD]->(sq)

            MERGE (t:Team {id: $event.team.id})
            MERGE (e)-[:TEAM]->(t)


            MERGE (possession:Possession {id: $match_id +'--'+ right('0000'+ $event.possession, 4)})
            MERGE (e)-[:POSSESSION]->(possession)
            MERGE (possession)-[:IN_PERIOD]->(mp)
            MERGE (possession)-[:MATCH]->(m)

            MERGE (pt:Team {id: $event.possession_team.id})
            ON CREATE SET pt.name = $event.possession_team.name
            MERGE (e)-[:POSSESSION_TEAM]->(pt)
            MERGE (possession)-[:TEAM]->(pt)

            FOREACH (_ IN CASE WHEN $event.under_pressure THEN [1] ELSE [] END |
                SET e:UnderPressure
            )

            FOREACH (_ IN CASE WHEN $event.position IS NOT NULL THEN [1] ELSE [] END |
                MERGE (position:Position {id: $event.position.id})
                ON CREATE SET position.name = $event.position.name
                MERGE (e)-[:POSITION]->(position)
            )

            WITH e

            CALL apoc.create.addLabels(e, [
                CASE WHEN $event.type.name = '50/50'
                    THEN 'FiftyFifty'
                    ELSE apoc.text.upperCamelCase($event.type.name)
                END
            ])
            YIELD node
            RETURN true
   """,
        match_id=match_id,
        event=event,
        properties=properties,
    ).consume()

    if event["type"]["name"] not in _specific_events:
        return not_implemented(tx, match_id, event)

    if _specific_events[event["type"]["name"]] != None:
        return _specific_events[event["type"]["name"]](tx, match_id, event).consume()

def import_events(tx, match_id, rows):
    try:
        for event in rows:
            import_event(tx, match_id=match_id, event=event)
    except Neo4jError as e:
        print(event)
        raise e

def link_events(tx, match_id):
    return tx.run(
        """
            MATCH (m:Match {id: $match_id})<-[:MATCH]-(e:Event)
            WHERE not e:OutOfSequence
            WITH m, e ORDER BY e.index ASC
            WITH m, collect(e) AS events

            FOREACH (e IN events |
                FOREACH (r IN [(e)-[r:NEXT_EVENT]->() | r] | DELETE r)
            )

            WITH events
            UNWIND range(0, size(events)-2) AS idx
            WITH events[idx] AS this, events[idx+1] AS next
            MERGE (this)-[:NEXT_EVENT]->(next)
        """,
        match_id=match_id,
    )

def link_possessions(tx, match_id):
    return tx.run(
        """
            MATCH (m:Match {id: $match_id})<-[:MATCH]-(p:Possession)

            WITH m, p ORDER BY p.index ASC
            WITH m, collect(p) AS possessions

            WITH m, possessions, possessions[0] AS first, possessions[ size(possessions)-1 ] AS last

            MERGE (m)-[:FIRST_POSSESSION]->(first)
            MERGE (m)-[:LAST_POSSESSION]->(last)

            WITH possessions

            UNWIND range(0, size(possessions)-2) AS idx
            WITH possessions[idx] AS this, possessions[idx+1] AS next
            MERGE (this)-[:NEXT_POSSESSION]->(next)
        """,
        match_id=match_id,
    )

def create_possession_event_pointers(tx, match_id):
    return tx.run(
        """
            MATCH (:Match {id: $match_id})<-[:MATCH]-(p:Possession)<-[:POSSESSION]-(e:Event),
                (p)-[:TEAM]->(t)
            WITH p, t, e ORDER BY e.index ASC
            WITH p, t, collect(e) AS events
            WITH p, t, events, [ e in events where (e)-[:TEAM]->(t) ] AS teamEvents

            WHERE size(teamEvents) > 0

            WITH p,
                events[0] AS first, events[-1] AS last,
                teamEvents[0] AS teamFirst, teamEvents[-1] AS teamLast

            MERGE (p)-[:FIRST_EVENT]->(first)
            MERGE (p)-[:LAST_EVENT]->(last)

            MERGE (p)-[:FIRST_POSSESSION_TEAM_EVENT]->(teamFirst)
            MERGE (p)-[:LAST_POSSESSION_TEAM_EVENT]->(teamLast)
        """,
        match_id=match_id,
    )

def link_out_of_sequence(tx, match_id):
    return tx.run(
        """
            MATCH (:Match {id: $match_id})<-[:MATCH]-(e:OutOfSequence),
                (prev)-[pr:NEXT_EVENT]->(e),
                (e)-[nr:NEXT_EVENT]->(next)

            DELETE pr, nr

            MERGE (prev)-[:NEXT_EVENT]->(n)

            FOREACH (_ IN CASE WHEN e:Pressure THEN [1] ELSE [] END |
                MERGE (prev)-[:PRESSURE]->(e)
            )

            FOREACH (_ IN CASE WHEN e:DribbledPast THEN [1] ELSE [] END |
                MERGE (prev)-[:DRIBBLED_PAST]->(e)
            )

            FOREACH (_ IN CASE WHEN toLower(e.outcome) contains 'lost' THEN [1] ELSE [] END |
                MERGE (prev)-[:WON_AGAINST]->(e)
            )
        """,
        match_id=match_id,
    )

def update_game_state(session, match_id, batch_size=5000):
    return session.run(
        """
            MATCH (:Match {id: $match_id})<-[:MATCH]-(e:Event)
            WITH m, e ORDER BY e.index ASC
            WITH m, collect(e) AS events

            WITH m, events,
                [(m)-[:HOME_TEAM]->(t) | t][0] as homeTeam,
                [(m)-[:AWAY_TEAM]->(t) | t][0] AS awayTeam,
                [e in events where e:Goal | {event:e, team: [(e)-[:TEAM]->(t) | t][0]} ] AS goals

            UNWIND events AS e

            CALL {
                WITH m, e, homeTeam, awayTeam, goals
                WITH *, [(e)-[:TEAM]->(t) | t ][0] AS eventTeam

                WITH m, e, goals, homeTeam, awayTeam, eventTeam,
                    [ g in goals where g.event.index < e.index AND g.team = eventTeam ] AS teamGoalsBefore,
                    [ g in goals where g.event.index < e.index AND g.team <> eventTeam ] AS oppositionGoalsBefore,
                    size([ g in goals where g.event.index < e.index AND g.team = homeTeam ]) AS homeTeamGoalsBefore,
                    size([ g in goals where g.event.index < e.index AND g.team <> awayTeam ]) AS awayTeamGoalsBefore

                WITH *,
                    goals, size(teamGoalsBefore) AS teamGoalsBefore, size(oppositionGoalsBefore) AS oppositionGoalsBefore

                SET e.game_state = CASE
                        WHEN teamGoalsBefore > oppositionGoalsBefore THEN 'Winning'
                        WHEN teamGoalsBefore < oppositionGoalsBefore THEN 'Losing'
                    ELSE 'Drawing' END,
                    e.goals_for = teamGoalsBefore,
                    e.goals_against = oppositionGoalsBefore,
                    e.home_score = homeTeamGoalsBefore,
                    e.away_score = awayTeamGoalsBefore

                FOREACH (_ IN CASE WHEN eventTeam = homeTeam THEN [1] ELSE [] END |
                    SET e:HomeEvent
                )
                FOREACH (_ IN CASE WHEN eventTeam = awayTeam THEN [1] ELSE [] END |
                    SET e:AwayEvent
                )

            } IN TRANSACTIONS OF $batch_size ROWS

            RETURN count(*) AS count
        """,
        match_id=match_id, batch_size=batch_size
    )

def update_thirds(session, match_id, batch_size=5000):
    return session.run(
        """
            MATCH (:Match {id: $match_id})<-[:MATCH]-(e:Event)
            WHERE e.locations IS NOT NULL
            CALL {
                WITH e
                WITH CASE WHEN e.location.x > 80 THEN 'AttackingThird'
                    WHEN e.location.x > 40 THEN 'MiddleThird'
                    ELSE 'DefensiveThird' END as third
                CALL apoc.create.addLabels(e, [third]) YIELD node
                RETURN count(*) AS count
            } IN TRANSACTIONS OF $batch_size ROWS
            RETURN count(*) AS count
        """,
        match_id=match_id, batch_size=batch_size
    )

def update_starting_formation(session):
    return session.run("""
        MATCH (t:Team)<-[r:HOME_TEAM|AWAY_TEAM]-(m)<-[:MATCH]-(e:StartingXi)-[:TEAM]->(t)
        SET r.formation = e.formation
    """)

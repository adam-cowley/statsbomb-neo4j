// 303451 => 2019-12-07 - Barcelona 5 - 2 Mallorca
MATCH (m:Match)<-[:HAS_MATCH|HAS_MATCH_WEEK|HAS_COMPETITION_STAGE*3]-(s)
// WHERE m.id = 16173
WHERE NOT exists((m)<-[:HOME_SQUAD_FOR|AWAY_SQUAD_FOR]-()-[:APPEARED_IN_SQUAD]->())
CALL apoc.load.json('file:///lineups/'+ m.id +'.json') YIELD value

// RETURN distinct(keys(value))
// ["lineup", "team_id", "team_name"]

// Squad for Match
MERGE (q:Squad {id: m.id + '--'+ value.team_id})

WITH *

UNWIND value.lineup AS player

// Player
MERGE (p:Player {id: player.player_id})
// ON CREATE
SET p.name = player.player_name,
    p.nickname = player.player_nickname

// Player Country
MERGE (pc:Country {id: player.country.id})
    ON CREATE SET pc.name = player.country.name

    MERGE (p)-[:FROM_COUNTRY]->(pc)

// Appearance
MERGE (a:Appearance {id: m.id + '--'+ p.id})
// ON CREATE
SET a.name = player.player_name + ': '+ m.name
MERGE (p)-[:HAS_APPEARANCE]->(a)
MERGE (a)-[:IN_SEASON]->(s)

// Player appeared in club season
MERGE (a)-[tsr:IN_SQUAD]->(q)
SET tsr.number = player.jersey_number

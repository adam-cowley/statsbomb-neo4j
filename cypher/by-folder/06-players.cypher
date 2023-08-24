CALL apoc.load.directory('*.json', 'lineups')
YIELD value AS filename

CALL apoc.load.json(filename)
YIELD value

UNWIND value.lineup AS player

MERGE (p:Player {id: player.player_id})
SET p.name = player.player_name,
    p.nickname = player.player_nickname

MERGE (c:Country {id: player.country.id})
ON CREATE SET c.name = player.country.name

MERGE (p)-[:REPRESENTS_COUNTRY]->(c)

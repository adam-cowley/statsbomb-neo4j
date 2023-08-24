// TODO: Currently only loading La Liga 2019/2020
CALL apoc.load.directory('*.json', 'matches/11')
YIELD value AS filename
WHERE filename CONTAINS '42'
CALL apoc.load.json(filename) YIELD value

WITH distinct value.referee AS referee
WHERE referee IS NOT NULL

MERGE (p:Person {id: referee.id})
SET p:Referee, p.name = referee.name

MERGE (c:Country {name: referee.country.name})

MERGE (p)-[:FROM_COUNTRY]->(c);
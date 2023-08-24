// TODO: Currently only loading La Liga 2019/2020
CALL apoc.load.directory('*.json', 'matches/11')
YIELD value AS filename
WHERE filename CONTAINS '42'
CALL apoc.load.json(filename) YIELD value

WITH distinct value.stadium AS stadium

MERGE (s:Stadium {id: stadium.id})
SET s.name = stadium.name

MERGE (c:Country {name: stadium.country.name})

MERGE (s)-[:IN_COUNTRY]->(c);
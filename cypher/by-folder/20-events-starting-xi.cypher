// TODO: All matches
MATCH (m:Match {id: 303725})<-[:HAS_MATCH]-()<-[:HAS_WEEK]-()<-[:HAS_STAGE]-(s)

WITH m, [ (m)-[:HOME_TEAM]->(t) | t.id ][0] AS homeTeamId, [ (m)-[:AWAY_TEAM]->(t) | t.id ][0] AS awayTeamId

CALL apoc.load.json('events/'+m.id+'.json')
YIELD value AS event

// "type": { "name": "Starting XI", "id": 35 }
WHERE event.type.id = 35

MATCH (t:Team { id: event.team.id })

MATCH (sq:Squad { id: m.id +'--'+ event.team.id })

RETURN *
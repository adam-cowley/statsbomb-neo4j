CALL apoc.load.directory('*.json', 'lineups')
YIELD value AS filename

CALL apoc.load.json(filename)
YIELD value

WITH filename, value, toInteger(apoc.text.split(filename, '[^\w]')[1]) AS matchId


MATCH (m:Match {id: matchId})<-[:HAS_MATCH]-()<-[:HAS_WEEK]-()<-[:HAS_STAGE]-(s),
    (m)-[:HOME_TEAM]->(home),
    (m)-[:AWAY_TEAM]->(away)



// Team
MERGE (t:Team {id: value.team_id})
ON CREATE SET t.name = value.team_name

// Team Season
MERGE (ts:TeamSeason {id: apoc.text.join([
    toString(t.id),
    toString(s.id)
], '--')})
SET ts.name = t.name + ' - ' + s.name

// Match Squad
MERGE (sq:Squad {id: apoc.text.join([
    toString(m.id),
    toString(t.id)
], '--')})
SET sq.name = t.name +': '+ m.name


MERGE (t)-[:HAS_TEAM_SEASON]->(ts)
MERGE (ts)-[:IN_SEASON]->(s)

MERGE (ts)-[:HAS_SQUAD]->(sq)

WITH *

CALL apoc.merge.relationship(
    m,
    CASE WHEN t.id = home.id THEN 'HOME_SQUAD' ELSE 'AWAY_SQUAD' END,
    {},
    {},
    sq,
    {}
) YIELD rel

RETURN *

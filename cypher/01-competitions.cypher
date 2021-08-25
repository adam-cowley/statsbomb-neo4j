CALL apoc.load.json('file:///competitions.json')
YIELD value
MERGE (c:Competition {id: value.competition_id})
SET c.name = value.competition_name;


CALL apoc.load.json('file:///competitions.json')
YIELD value
MATCH (c:Competition {id: value.competition_id})
MERGE (s:Season {id: value.competition_id +'--'+ value.season_id, competition_id: value.competition_id, season_id: value.season_id})
SET s.name = value.competition_name +' - '+ value.season_name
MERGE (c)-[:HAS_SEASON]->(s);

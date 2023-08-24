MATCH (mx:Match)<-[:HAS_MATCH]-(mw)<-[:HAS_MATCH_WEEK]-(s)<-[:HAS_COMPETITION_STAGE]-(sx)
WHERE NOT exists((mx)-[:HAS_REFEREE]->())

WITH * LIMIT 1


CALL apoc.load.json('file:///matches/'+ sx.competition_id + '/'+ sx.season_id +'.json') YIELD value

MATCH (m:Match {id: value.match_id})

MERGE (r:Referee { id: coalesce(value.referee.id, 'UNKNOWN') })
ON CREATE SET r.name = value.referee.name

// -> Referee Country
MERGE (rc:Country {id: coalesce(value.referee.country.id, 'UNKNOWN')})
ON CREATE SET rc.name = value.referee.country.name

MERGE (m)-[:HAS_REFEREE]->(r)
MERGE (r)-[:FROM_COUNTRY]->(rc);
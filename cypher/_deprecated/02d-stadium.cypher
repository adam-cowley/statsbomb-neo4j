MATCH (m:Match)
WHERE NOT exists((m)-[:AT_STADIUM]->())

CALL apoc.load.json('file:///matches/'+ m.competition_id + '/'+ m.season_id +'.json') YIELD value

MATCH (m:Match {id: value.match_id})

MERGE (st:Stadium {id: value.stadium.id})
ON CREATE SET st.name = value.stadium.name

// -> Stadium Country
MERGE (stc:Country {id: value.stadium.country.id})
ON CREATE SET stc.name = value.stadium.country.name

MERGE (st)-[:IN_COUNTRY]->(stc)

MERGE (m)-[:AT_STADIUM]->(st);
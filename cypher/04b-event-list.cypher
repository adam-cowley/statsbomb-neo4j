MATCH (:Event)-[r:NEXT_EVENT]->()
DELETE r;

MATCH (m:Match)-[:HAS_PERIOD]->(mp)<-[:HAS_EVENT]->(e)
WITH mp, e ORDER BY e.index ASC
WITH mp, collect(e) AS events
CALL apoc.nodes.link(events, 'NEXT_EVENT')
RETURN count(*);

MATCH (e:Event)-[:SUBJECT]->(s)<-[:HAS_APPEARANCE]-(p)
SET e.caption = coalesce(p.nickname, p.name) +' '+ e.type;

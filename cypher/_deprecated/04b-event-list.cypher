// Delete Next Event
MATCH (:Event)-[r:NEXT_EVENT]->()
DELETE r;



// Set temporary label for each
MATCH (mp:PatchPeriod) SET mp:NotLinked;

// Collect events by match period and link
CALL apoc.periodic.commit("
    MATCH (mp:NotLinked)
    WITH mp LIMIT 1

    MATCH (mp)-[:HAS_EVENT]->(e)
    WITH mp, e ORDER BY e.index ASC
    WITH mp, collect(e) AS events

    REMOVE mp:NotLinked
    WITH events

    CALL apoc.nodes.link(events, 'NEXT_EVENT')
    RETURN count(*)
", {});


// Set Event Caption
MATCH (e:Event)-[:SUBJECT]->(s)<-[:HAS_APPEARANCE]-(p)
SET e.caption = coalesce(p.nickname, p.name) +' '+ e.type;

// Delete Next Event
MATCH (:Event)-[r:NEXT_EVENT]->()
DELETE r;

// Collect events by match period
CALL apoc.periodic.iterate("
    MATCH (mp:MatchPeriod)<-[:HAS_EVENT]->(e)
    WITH mp, e ORDER BY e.index ASC
    RETURN mp, collect(e) AS events
", "
    CALL apoc.nodes.link(events, 'NEXT_EVENT')
    RETURN distinct true
", {
    parallel: true,
    iterateList: true,
    batchSize: 1000
});

// Set Event Caption
MATCH (e:Event)-[:SUBJECT]->(s)<-[:HAS_APPEARANCE]-(p)
SET e.caption = coalesce(p.nickname, p.name) +' '+ e.type;

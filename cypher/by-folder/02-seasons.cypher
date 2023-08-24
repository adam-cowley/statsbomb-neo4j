// TODO: Currently only loading La Liga 2019/2020
CALL apoc.load.directory('*.json', 'matches/11')
YIELD value AS filename
WHERE filename CONTAINS '42'
CALL apoc.load.json(filename) YIELD value


WITH
    value.competition.competition_id AS competition_id,
    value.season AS season,
    {
        id: apoc.text.join([
            toString(value.competition.competition_id),
            toString(value.season.season_id),
            toString(value.competition_stage.id)
        ], '--'),
        name: value.competition_stage.name,
        weeks: collect(distinct value.match_week)
     } AS stage

WITH competition_id, season, collect(distinct stage) AS stages

MATCH (c:Competition {id: competition_id})

MERGE (s:Season {id: competition_id +'--'+ season.season_id})
MERGE (c)-[:HAS_SEASON]->(s)

FOREACH (stage IN stages |
    MERGE (st:SeasonStage {id: stage.id})
    SET st.name = c.name + ': '+ stage.name

    MERGE (s)-[:HAS_STAGE]->(st)

    FOREACH (week IN stage.weeks |
        MERGE (mw:MatchWeek {id: st.id + '--'+ week})
        SET mw.name = st.name + ': Week '+ week

        MERGE (st)-[:HAS_WEEK]->(mw)
    )
);


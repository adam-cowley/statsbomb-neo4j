MATCH (sx:Season {season_id: 42, competition_id: 11 })
// MATCH (sx:Season)
// WHERE NOT exists((sx)-[:HAS_COMPETITION_STAGE]->())


CALL apoc.load.json('file:///matches/'+ sx.competition_id + '/'+ sx.season_id +'.json') YIELD value

WITH distinct sx, value.competition AS competition, value.season AS season, value.competition_stage AS stage,
    collect(distinct value.match_week) AS weeks

MERGE (s:CompetitionStage {
    id: sx.id + '--'+ stage.id,
    competition_id: competition.competition_id,
    season_id: season.season_id,
    number: stage.id
})
ON CREATE SET s.name = competition.competition_name + ' - ' + season.season_name + ': '+ stage.name

MERGE (sx)-[:HAS_COMPETITION_STAGE]->(s)

FOREACH (week IN weeks |
    MERGE (w:MatchWeek {
        id: s.id + '--' + week,
        competition_id: competition.competition_id,
        season_id: season.season_id,
        matchweek: week
    })
    ON CREATE SET w.name = competition.competition_name + ' - ' + season.season_name + ': Week '+ week

    MERGE (s)-[:HAS_MATCH_WEEK]->(w)
);
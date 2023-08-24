MATCH (sx:Season {season_id: 42, competition_id: 11 })
// MATCH (sx:Season)
// WHERE NOT exists((sx)-[:HAS_COMPETITION_STAGE]->())


CALL apoc.load.json('file:///matches/'+ sx.competition_id + '/'+ sx.season_id +'.json') YIELD value

WITH distinct sx, value, value.competition AS competition, value.season AS season, value.competition_stage AS stage, value.match_week AS week

MATCH (s:CompetitionStage {id: sx.id + '--'+ stage.id})
MATCH (w:MatchWeek {id: s.id + '--' + week})



// Match
MERGE (m:Match {id: value.match_id})
// ON CREATE
SET
    m.competition_id = competition.competition_id,
    m.season_id = season.season_id,
     m.name = CASE WHEN exists(value.home_score) AND exists(value.away_score)
    THEN
        value.match_date + ' - ' + value.home_team.home_team_name + ' '+ value.home_score + ' - ' + value.away_score + ' ' + value.away_team.away_team_name
    ELSE
        value.match_date + ' - ' + value.home_team.home_team_name + ' vs ' + value.away_team.away_team_name
    END,
    m.kickoff = localdatetime(value.match_date + 'T' + value.kick_off),
    m.homeGoals = value.home_score,
    m.awayGoals = value.away_score,

// SET
    m.updatedAt = localdatetime(value.last_updated),
    m.status = value.match_status

MERGE (w)-[:HAS_MATCH]->(m);
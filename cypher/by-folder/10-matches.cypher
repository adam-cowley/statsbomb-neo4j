// TODO: Currently only loading La Liga 2019/2020
CALL apoc.load.directory('*.json', 'matches/11')
YIELD value AS filename
WHERE filename CONTAINS '42'
CALL apoc.load.json(filename) YIELD value

MATCH (mw:MatchWeek {
    id: apoc.text.join([
        toString(value.competition.competition_id),
        toString(value.season.season_id),
        toString(value.competition_stage.id),
        toString(value.match_week)
    ], '--')
})

MATCH (stadium:Stadium {id: value.stadium.id})
MATCH (home:Team {id: value.home_team.home_team_id})
MATCH (away:Team {id: value.away_team.away_team_id})
MATCH (referee:Referee {id: value.referee.id})


MERGE (m:Match {id: value.match_id})
SET m.competition = value.competition.competition_id,
    m.season = value.season.season_id,
    m.name =
    CASE
        WHEN value.home_score IS NOT NULL AND value.away_score IS NOT NULL
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

MERGE (mw)-[:HAS_MATCH]->(m)


// Stadium
MERGE (m)-[:IN_STADIUM]->(stadium)

// Referee
MERGE (m)-[:REFEREE]->(referee)

// Home Team
MERGE (m)-[hr:HOME_TEAM]->(home)
SET hr.goals = value.home_score,
    hr.outcome = CASE
        WHEN value.home_score < value.away_score THEN 'LOSS'
        WHEN value.home_score > value.away_score THEN 'WIN'
        ELSE 'DRAW'
        END

// AWay Team
MERGE (m)-[ar:AWAY_TEAM]->(away)
SET ar.goals = value.away_score,
    ar.outcome = CASE
        WHEN value.home_score > value.away_score THEN 'LOSS'
        WHEN value.home_score < value.away_score THEN 'WIN'
        ELSE 'DRAW'
        END

RETURN *
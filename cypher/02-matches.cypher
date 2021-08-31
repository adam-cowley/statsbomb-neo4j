// La Liga 2019-2020
// MATCH (sx:Season {season_id: 42, competition_id: 11 })
MATCH (sx:Season)
WHERE NOT exists((sx)-[:HAS_COMPETITION_STAGE]->())

CALL apoc.load.json('file:///matches/'+ sx.competition_id + '/'+ sx.season_id +'.json') YIELD value

// RETURN distinct(keys(value))
// ["match_week", "last_updated", "metadata", "home_score", "match_status_360", "away_score", "match_id", "last_updated_360", "competition", "competition_stage", "referee", "match_status", "match_date", "away_team", "season", "stadium", "kick_off", "home_team"]

// Competition Stage
MERGE (s:CompetitionStage {
    id: sx.id + '--'+ value.competition_stage.id,
    competition_id: value.competition.competition_id,
    season_id: value.season.season_id,
    number: value.competition_stage.id
})
ON CREATE SET s.name = value.competition.competition_name + ' - ' + value.season.season_name + ': Week '+ value.competition_stage.name

MERGE (sx)-[:HAS_COMPETITION_STAGE]->(s)

// Match Week
MERGE (w:MatchWeek {
    id: s.id + '--' + value.match_week,
    competition_id: value.competition.competition_id,
    season_id: value.season.season_id,
    matchweek: value.match_week
})
ON CREATE SET w.name = value.competition.competition_name + ' - ' + value.season.season_name + ': '+ value.match_week

MERGE (s)-[:HAS_MATCH_WEEK]->(w)

// Match
MERGE (m:Match {id: value.match_id})
// ON CREATE
SET m.name = CASE WHEN exists(value.home_score) AND exists(value.away_score)
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

MERGE (w)-[:HAS_MATCH]->(m)

// Referee
// FOREACH (_ IN CASE WHEN value.referee.id IS NOT NULL THEN [1] ELSE [] END |
//     MERGE (r:Referee { id: value.referee.id })
//     ON CREATE SET r.name = value.referee.name

//     // -> Referee Country
//     MERGE (rc:Country {id: value.referee.country.id})
//     ON CREATE SET rc.name = value.referee.country.name

//     MERGE (r)-[:FROM_COUNTRY]->(rc)
//     MERGE (m)-[:HAS_REFEREE]->(r)
// )


// Stadium
FOREACH (_ IN CASE WHEN value.stadium IS NOT NULL THEN [1] ELSE [] END |
    MERGE (st:Stadium {id: value.stadium.id})
    ON CREATE SET st.name = value.stadium.name

    // -> Stadium Country
    MERGE (stc:Country {id: value.stadium.country.id})
    ON CREATE SET stc.name = value.stadium.country.name

    MERGE (st)-[:IN_COUNTRY]->(stc)

    MERGE (m)-[:AT_STADIUM]->(st)
)


// Home Team
MERGE (ht:Team {id: value.home_team.home_team_id, gender: value.home_team.home_team_gender})
ON CREATE SET ht.name = value.home_team.home_team_name,
    ht.fullName = value.home_team.home_team_name +' ('+ value.home_team.home_team_gender +')'

// -> Home Team Country
MERGE (htc:Country {id: value.home_team.country.id})
ON CREATE SET htc.name = value.home_team.country.name

MERGE (ht)-[:IN_COUNTRY]->(htc)

// Home Team Season
MERGE (hts:TeamSeason {id: sx.id + '--'+ ht.id})
// ON CREATE
SET hts.name = ht.name + ': '+ sx.name
MERGE (ht)-[:HAS_SEASON]->(hts)
MERGE (hts)-[:IN_SEASON]->(sx)


// -> Home Team Squad
MERGE (htsq:Squad {id: m.id + '--'+ ht.id})
SET htsq.name = toString(m.kickoff) + ': '+ ht.name +' (Home vs. '+ value.away_team.away_team_name +')'
MERGE (hts)-[:HAS_SQUAD]->(htsq)

// -> Fixture
MERGE (htsq)-[htr:HOME_TEAM_FOR]->(m)
SET htr.goals = value.home_score


// -> Home Team Manager
FOREACH (manager IN value.home_team.managers |
    MERGE (p:Person {id: manager.id})
    ON CREATE SET p.name = manager.name,
        p.nickname = manager.nickname,
        p.dob = date(manager.dob)

    MERGE (mn:ManagerSeason {id: sx.id  + '--'+ manager.id })
    SET mn.name = manager.name +': '+ sx.name

    MERGE (p)-[:WAS_MANAGER]->(mn)
    MERGE (mn)-[:FOR_SEASON]->(sx)
    MERGE (mn)-[:FOR_TEAM]->(ht)

    MERGE (mn)-[:HOME_MANAGER_FOR]->(m)

    // -> away Team Manager Country
    MERGE (pc:Country {id: manager.country.id})
    ON CREATE SET pc.name = manager.country.name

    MERGE (p)-[:FROM_COUNTRY]->(pc)
)


// Away Team
MERGE (at:Team {id: value.away_team.away_team_id, gender: value.away_team.away_team_gender})
ON CREATE SET at.name = value.away_team.away_team_name,
    at.fullName = value.away_team.away_team_name +' ('+ value.away_team.away_team_gender +')'

// -> away Team Country
MERGE (atc:Country {id: value.away_team.country.id})
ON CREATE SET atc.name = value.away_team.country.name

MERGE (at)-[:IN_COUNTRY]->(atc)

// Away Team Season
MERGE (ats:TeamSeason {id: sx.id + '--'+ at.id})

// ON CREATE
SET ats.name = at.name + ': '+ sx.name
MERGE (at)-[:HAS_SEASON]->(ats)
MERGE (ats)-[:IN_SEASON]->(sx)

// -> Home Team Squad
MERGE (atsq:Squad {id: m.id + '--'+ at.id})
SET atsq.name = toString(m.kickoff) + ': '+ at.name +' (Away vs. '+ ht.name +')'
MERGE (ats)-[:HAS_SQUAD]->(atsq)

// -> Fixture
MERGE (atsq)-[r:AWAY_TEAM_FOR]->(m)
SET r.goals = value.away_score

// -> away Team Manager
FOREACH (manager IN value.away_team.managers |
    MERGE (p:Person {id: manager.id})
    ON CREATE SET p.name = manager.name,
        p.nickname = manager.nickname,
        p.dob = date(manager.dob)

    MERGE (mn:ManagerSeason {id: sx.id  + '--'+ manager.id })
    SET mn.name = manager.name +': '+ sx.name

    MERGE (p)-[:WAS_MANAGER]->(mn)
    MERGE (mn)-[:FOR_SEASON]->(sx)
    MERGE (mn)-[:FOR_TEAM]->(at)

    MERGE (mn)-[:AWAY_MANAGER_FOR]->(m)

    // -> away Team Manager Country
    MERGE (pc:Country {id: manager.country.id})
    ON CREATE SET pc.name = manager.country.name

    MERGE (p)-[:FROM_COUNTRY]->(pc)
)

RETURN count(*);
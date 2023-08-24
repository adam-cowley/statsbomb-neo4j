// TODO: Currently only loading La Liga 2019/2020
CALL apoc.load.directory('*.json', 'matches/11')
YIELD value AS filename
WHERE filename CONTAINS '42'
CALL apoc.load.json(filename) YIELD value

UNWIND [
    {
        id: value.home_team.home_team_id,
        name: value.home_team.home_team_name,
        gender: value.home_team.home_team_gender,
        group: value.home_team.home_team_group,
        managers: value.home_team.managers,
        country: value.home_team.country
    },
    {
        id: value.away_team.away_team_id,
        name: value.away_team.away_team_name,
        gender: value.away_team.away_team_gender,
        group: value.away_team.away_team_group,
        managers: value.away_team.managers,
        country: value.away_team.country
    }
] AS team


WITH distinct team

MERGE (t:Team {id: team.id})
SET t += team { .name, .gender, .group }

MERGE (c:Country {name: team.country.name})
MERGE (t)-[:COMPETES_IN_COUNTRY]->(c)

FOREACH (manager IN team.managers |
    MERGE (p:Person {
        id: manager.id
    })
    SET p += {
        name: manager.name,
        nickname: manager.nickname,
        dob: date(manager.dob)
    }
    SET p:Manager

    MERGE (c:Country {name: manager.country.name})
    MERGE (p)-[:FROM_COUNTRY]->(c)
)


RETURN t
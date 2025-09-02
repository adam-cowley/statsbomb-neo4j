
import os
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase
from lib.main import StatsbombNeo4j

load_dotenv()

os.environ["SB_USERNAME"] = "adam@adamcowley.co.uk"
os.environ["SB_PASSWORD"] = "F4uYc4K6"

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

driver.verify_connectivity()

sbn = StatsbombNeo4j(
    os.getenv('SB_USERNAME'),
    os.getenv('SB_PASSWORD'),
    driver
)

league_two = 5
# league_two_22_23 = 235
# league_two_23_24 = 281
league_two_24_25 = 317

# sbn.install_constraints()

sbn.import_matches(league_two, league_two_24_25)

sbn.import_player_season_stats(league_two, league_two_24_25)
sbn.import_team_season_stats(league_two, league_two_24_25)

# sbn.clear_events()

def get_next_matches():
    # Get next match without events
    records, _, __ = driver.execute_query("""
        MATCH (m:Match)
        WHERE m.kick_off <= datetime() AND not (m)<-[:MATCH]-(:Event)
            AND m.play_status <> 'Postponed'
        RETURN m.id AS id
        ORDER BY m.kick_off ASC
        LIMIT 100
    """)

    rows = len(records)

    if rows == 0:
        return

    for record in records:
        id = record.get('id')

        start = datetime.now()

        print(id, end="\t")
        sbn.import_lineups(id)

        added = sbn.import_events(id)

        print(added, end="\t")

        end = datetime.now()
        print(str((end - start)))

    return rows, added

# print(sbn.import_matches(league_two, league_two_23_24))

next, added = get_next_matches()
while next != None and added > 0:
    print(next)

    next, added = get_next_matches()


# print(sbn.import_competitions())

# print(sbn.import_competition_events(2, 235))

# print(sbn.import_events(3837579))
# print(sbn.import_events(3837558))
# print(sbn.import_events(3837342))

# print(sbn.import_lineups(3837342))

# sbn.install_constraints()

# sbn.import_competitions()



# for competition in sbn.competitions():
#     if competition["competition_name"].startswith("U") == False:
#         print(competition["competition_name"], competition["season_name"])
#         sbn.import_player_season_stats(competition["competition_id"], competition["season_id"])
#         sbn.import_team_season_stats(competition["competition_id"], competition["season_id"])

#         print(competition['competition_name'], competition['season_name'])



# for match in sbn.matches(5, 317):
#     print(match['match_id'])
#     sbn.import_lineups(match['match_id'])


driver.close()





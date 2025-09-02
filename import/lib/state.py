from neo4j import GraphDatabase, Result

DRAWING = 'drawing'
WINNING = 'winning'
LOSING = 'losing'

if __name__ == "__main__":
    import os
    import json
    from datetime import datetime
    from dotenv import load_dotenv

    load_dotenv()

    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )

    driver.verify_connectivity()

    matches = driver.execute_query("""
        MATCH (m:Match)
        WHERE (m)<-[:MATCH]-(:Event)
        RETURN m.id AS id,
            [ (m)-[:HOME_TEAM]->(t) | t.name][0] AS home_team,
            [ (m)-[:AWAY_TEAM]->(t) | t.name][0] AS away_team
    """, result_transformer_=lambda res: [
        (row['id'], row['home_team'], row['away_team'])
        for row in res
    ])

    for id, home_team, away_team in matches:
        events = driver.execute_query("""
            MATCH (m:Match {id: $id})<-[:MATCH]-(e:Event)
            RETURN e { .id, .type, .outcome, .index, timestamp: toString(e.timestamp) } as event,
            [ (e)-[:TEAM]->(p) | p.name ][0] AS team,
            [ (e)-[:PLAYER]->(p) | p { .id, .name } ][0] AS player
            ORDER BY e.index ASC
        """, id=id, result_transformer_=lambda res: [ dict(row) for row in res] )

        home_score = 0
        away_score = 0

        # Calculate game states
        updates = []

        for row in events:
            home_or_away = "home" if row['team'] == home_team else "away"
            event = row['event']

            # Game state at time of event
            state = DRAWING

            team_score = 0
            opposition_score = 0

            if row['team'] == home_team:
                team_score = home_score
                opposition_score = away_score

                if home_score > away_score:
                    state = WINNING
                elif away_score > home_score:
                    state = LOSING
            else:
                team_score = away_score
                opposition_score = home_score

                if away_score > home_score:
                    state = WINNING
                elif home_score > away_score:
                    state = LOSING

            # Increment scoring?
            if event['type'] == "Shot" and 'outcome' in event and event['outcome'] == "Goal":
                if row['team'] == home_team:
                    home_score += 1
                else:
                    away_score += 1

            elif event['type'] == "Own Goal Against":
                if row['team'] == home_team:
                    away_score += 1
                else:
                    home_score += 1


            updates.append({
                "id": event['id'],
                "home_or_away": home_or_away,
                "home_score": home_score,
                "away_score": away_score,
                "state": state,
                "team_score": team_score,
                "opposition_score": opposition_score,
            })

        # Save game state
        driver.execute_query("""
            UNWIND $rows AS row
            MATCH (e:Event {id: row.id})
            SET e += row
        """, rows=updates)

    driver.close()


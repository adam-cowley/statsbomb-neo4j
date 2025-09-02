from neo4j import Driver
import pandas as pd
from statsbombpy import sb
from itertools import groupby
from lib.db import tx
from lib.stats import team_season_stats

class StatsbombNeo4j:
    def __init__(self, sb_user: str, sb_passpwd: str, driver: Driver) -> None:
        self.creds = {
            "user": sb_user,
            "passwd": sb_passpwd
        }
        self.driver = driver

    def install_constraints(self):
        from lib.db.constraints import constraints

        for statement in constraints:
            self.driver.execute_query(statement)

        return len(constraints)

    def competitions(self):
        competitions = sb.competitions(fmt="list", creds=self.creds)

        return list(competitions.values())

    def import_competitions(self):
        competitions = self.competitions()

        with self.driver.session() as session:
            res = session.execute_write(tx.import_competitions, competitions=competitions)
            return res

    def matches(self, competition_id, season_id):
        matches = sb.matches(competition_id=competition_id, season_id=season_id, fmt="list", creds=self.creds)

        return list(matches.values())

    def import_matches(self, competition_id, season_id):
        matches = self.matches(competition_id, season_id)

        return self._batch_write(
            tx.import_matches,
            matches,
            100,
            competition_id=competition_id,
            season_id=season_id
        )

    def events(self, match_id):
        events = sb.events(match_id=match_id, fmt="dict", creds=self.creds)

        return list(events.values())

    def import_events(self, match_id):
        events = self.events(match_id=match_id)

        self._batch_write(
            tx.import_events,
            events,
            500,
            match_id = match_id,
        )

        self._link_events(match_id)

        return len(events)

    def _link_events(self, match_id):
        with self.driver.session() as session:
            session.execute_write(tx.link_events, match_id=match_id)
            session.execute_write(tx.link_possessions, match_id=match_id)
            session.execute_write(tx.create_possession_event_pointers, match_id=match_id)
            session.execute_write(tx.link_out_of_sequence, match_id=match_id)

    def competition_events(self, competition_id, season_id):
        competitions = self.competitions()
        competition = next(competition for competition in competitions if competition['competition_id'] == competition_id and competition['season_id'] == season_id)

        all_events = sb.competition_events(competition['country_name'], competition['competition_name'], competition['season_name'], competition['competition_gender'], creds=self.creds)

        return list(all_events.values())

    def import_competition_events(self, competition_id, season_id, batch_size=5000):
        all_events = self.competition_events(competition_id, season_id)

        # Group by match
        by_match = groupby(all_events, lambda event: event['match_id'])

        for match_id, events in by_match:
            self._batch_write(
                tx.import_events,
                events,
                batch_size,
                match_id=match_id
            )

            with self.driver.session() as session:
                tx.update_game_state(session, match_id)
                tx.update_thirds(session, match_id)

        return len(all_events)

    def import_player_season_stats(self, competition_id, season_id):
        stats = sb.player_season_stats(competition_id=competition_id, season_id=season_id, fmt="list", creds=self.creds)

        with self.driver.session() as session:
            session.execute_write(tx.import_player_season_stats, stats=stats, competition_id=competition_id, season_id=season_id)

        return len(stats)

    def import_team_season_stats(self, competition_id, season_id):
        stats = sb.team_season_stats(competition_id=competition_id, season_id=season_id, creds=self.creds)

        exclude_rank = ['team_season_matches']

        rank_columns = {}

        for n in stats:
            # Find ascending or descending
            ascending = False

            try:
                stat = next((stat for stat in team_season_stats if stat['key'] == n))
                ascending = stat['ascending']
            except:
                pass

            if n.startswith('team_season') and n not in exclude_rank:
                rank_columns[ n + '_rank' ] = stats[n].rank(ascending=ascending)
                rank_columns[ n + '_percentile' ] = stats[n].rank(pct=True, ascending=ascending)

        rank_columns = pd.DataFrame(rank_columns)
        stats = pd.concat([ stats, rank_columns ], axis=1)

        stats = [ dict(row) for _, row in stats.iterrows() ]

        with self.driver.session() as session:
            session.execute_write(tx.import_team_seasons_stats, stats=stats, competition_id=competition_id, season_id=season_id)

        return len(stats)


    def lineups(self, match_id):
        return list(sb.lineups(match_id, fmt="dict", creds=self.creds).values())

    def import_lineups(self, match_id):
        lineups = self.lineups(match_id)

        with self.driver.session() as session:
            session.execute_write(tx.import_lineups, match_id=match_id, lineups=lineups)

    def _batch(self, iterable, batch_size=100):
        batch = []
        for item in iterable:
            batch.append(item)
            if len(batch) == batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def _batch_write(self, tx_fn, data, batch_size=100, **kwargs):
        with self.driver.session() as session:
            for rows in self._batch(data, batch_size):
                session.execute_write(tx_fn, rows=rows, **kwargs)
        return len(data)

    def clear_events(self):
        with self.driver.session() as session:
            session.run("""
                MATCH (e:Event)
                CALL {
                    WITH e
                    DETACH DELETE e
                } IN TRANSACTIONS OF 1000 rows
            """).consume()


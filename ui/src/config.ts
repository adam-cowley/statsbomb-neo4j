export const HOSTNAME = "https://data.statsbombservices.com"
export const VERSIONS = {
  "competitions": "v4",
  "matches": "v5",
  "lineups": "v4",
  "events": "v8",
  "360-frames": "v2",
  "player-match-stats": "v4",
  "player-season-stats": "v4",
  "team-season-stats": "v2",
}
export const OPEN_DATA_PATHS = {
    "competitions": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json",
    "matches": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{competition_id}/{season_id}.json",
    "lineups": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/lineups/{match_id}.json",
    "events": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json",
    "frames": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/three-sixty/{match_id}.json",
}
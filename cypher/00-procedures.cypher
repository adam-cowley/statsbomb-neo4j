CALL apoc.custom.asFunction(
    // name
    'matchWeekId',
    // statement
    '
        RETURN apoc.text.join([
            toString($input.competition.competition_id),
            toString($input.season.season_id),
            toString($input.competition_stage.id),
            toString($input.match_week)
        ], "--") AS id
    ',
    // outputs
    'STRING',
    // inputs
    [['input', 'MAP', '{
        competition: {competition_id: 1},
        season: {season_id: 2},
        competition_stage: {id: 3},
        match_week: 4
    }']],
    // single row
    true,
    // description
    'Generate the :MatchWeek.id property from a JSON object'
)
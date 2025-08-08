import sys
sys.path.append('./src')
from ScraperFC import Understat
from ScraperFC.understat import comps
from ScraperFC.scraperfc_exceptions import InvalidLeagueException, InvalidYearException

import random
import pandas as pd
import pytest
from contextlib import nullcontext as does_not_raise

class TestUnderstat:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('2019/2020', 'Ligue 1', does_not_raise()),
         (2020, 'Ligue 1', pytest.raises(TypeError)),
         ('fake year', 'Ligue 1', pytest.raises(InvalidYearException))]
    )
    def test_invalid_year(self, year, league, expected):
        us = Understat()
        with expected:
            us.get_season_link(year, league)
        with expected:
            us.get_match_links(year, league)
        with expected:
            us.get_team_links(year, league)
        with expected:
            us.scrape_season_data(year, league)
        with expected:
            us.scrape_league_tables(year, league)
        with expected:
            us.scrape_matches(year, league)
        with expected:
            us.scrape_all_teams_data(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('2023/2024', 'RFPL', does_not_raise()),
         ('2023/2024', {'league': 'RFPL'}, pytest.raises(TypeError)),
         ('2023/2024', 'fake league', pytest.raises(InvalidLeagueException))]
    )
    def test_invalid_league(self, year, league, expected):
        us = Understat()
        with expected:
            us.get_season_link(year, league)
        with expected:
            us.get_valid_seasons(league)
        with expected:
            us.get_match_links(year, league)
        with expected:
            us.get_team_links(year, league)
        with expected:
            us.scrape_season_data(year, league)
        with expected:
            us.scrape_league_tables(year, league)
        with expected:
            us.scrape_matches(year, league)
        with expected:
            us.scrape_all_teams_data(year, league)

    # ==============================================================================================
    def test_scrape_season_data(self):
        understat = Understat()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]

        season_data = understat.scrape_season_data(year, league)
        assert len(season_data) == 3
        assert isinstance(season_data[0], list)
        assert isinstance(season_data[1], dict)
        assert isinstance(season_data[2], list)

    # ==============================================================================================
    def test_scrape_league_tables(self):
        understat = Understat()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]

        tables = understat.scrape_league_tables(year, league)
        assert len(tables) == 3
        for x in tables:
            assert isinstance(x, pd.DataFrame)
            assert x.shape[0] > 0
            assert x.shape[1] > 0

    # ==============================================================================================
    def test_scrape_matches(self):
        understat = Understat()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]

        # Use as_df=True so we test that code
        matches = understat.scrape_matches(year, league, as_df=True)
        assert isinstance(matches, dict)

        first_key = list(matches.keys())[0]
        first_value = matches[first_key]
        assert isinstance(first_value['shots_data'], pd.DataFrame)
        assert isinstance(first_value['match_info'], pd.DataFrame)
        assert isinstance(first_value['rosters_data'], pd.DataFrame)

    # ==============================================================================================
    def test_scrape_all_teams_data(self):
        understat = Understat()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]

        # Use as_df=True so we test that code
        teams_data = understat.scrape_all_teams_data(year, league, as_df=True)
        assert isinstance(teams_data, dict)

        first_key = list(teams_data.keys())[0]
        first_value = teams_data[first_key]
        assert isinstance(first_value['matches'], pd.DataFrame)
        assert isinstance(first_value['team_data'], dict)
        for k, v in first_value['team_data'].items():
            assert isinstance(v, pd.DataFrame)
        assert isinstance(first_value['players_data'], pd.DataFrame)

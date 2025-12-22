import sys
import pandas as pd
import pytest
from contextlib import nullcontext as does_not_raise

sys.path.append('./src/')
from ScraperFC import ClubElo

class TestClubElo:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'team, date, expected',
        [(9, '2024-04-26', pytest.raises(TypeError)),
         ('FC Barcelona', '2024-04-26', pytest.raises(Exception))]
    )
    def test_invalid_team(self, team, date, expected):
        with expected:
            ClubElo().scrape_team_on_date(team, date)
        with expected:
            ClubElo().scrape_team(team)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'team, date, expected',
        [('Barcelona', 9, pytest.raises(TypeError)),
         ('Barcelona', '2024-04-06', does_not_raise()),
         ('Barcelona', '2024-4-06', does_not_raise()),
         ('Barcelona', '2024-4-6', does_not_raise()),
         ('Barcelona', '04-26-2024', pytest.raises(ValueError)),
         ('Barcelona', '24-04-09', pytest.raises(ValueError))]
    )
    def test_invalid_date(self, team, date, expected):
        with expected:
            ClubElo().scrape_team_on_date(team, date)
        with expected:
            ClubElo().scrape_date(date)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'team, date, expected',
        [('Barcelona', '1990-12-02', 1794.83435059),
         ('Barcelona', '1990-12-03', 1796.578125),
         ('Barcelona', '1990-12-06', 1796.578125),
         ('Barcelona', '1990-12-09', 1796.578125),
         ('Barcelona', '1990-12-10', 1806.16906738)]
    )
    def test_scrape_team_on_date(self, team, date, expected):
        actual = ClubElo().scrape_team_on_date(team, date)
        assert actual == expected

    # ==============================================================================================
    def test_scrape_fixtures(self):
        actual = ClubElo().scrape_fixtures()
        assert isinstance(actual, pd.DataFrame)
        assert actual.shape[0] > 0
        assert actual.shape[1] > 0

    # ==============================================================================================
    def test_scrape_team(self):
        actual = ClubElo().scrape_team('Arsenal')
        assert isinstance(actual, pd.DataFrame)
        assert actual.shape[0] > 0
        assert actual.shape[1] > 0

    # ==============================================================================================
    def test_scrape_date(self):
        actual = ClubElo().scrape_date('2024-04-06')
        assert isinstance(actual, pd.DataFrame)
        assert actual.shape[0] > 0
        assert actual.shape[1] > 0

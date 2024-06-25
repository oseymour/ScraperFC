import sys
sys.path.append('./src/')
from ScraperFC import FiveThirtyEight
from ScraperFC.scraperfc_exceptions import InvalidLeagueException, InvalidYearException

import pytest
import pandas as pd
from contextlib import nullcontext as does_not_raise


class TestFiveThirtyEight:

    @pytest.mark.parametrize(
        'year, league, expected',
        [(2020, 'La Liga', pytest.raises(InvalidLeagueException)),
         (2020, 9, pytest.raises(TypeError)),
         (2020, 'All', does_not_raise()),
         ({"a": 9}, "English League One", pytest.raises(TypeError))]
    )
    def test_invalid_league(self, year, league, expected):
        with expected:
            FiveThirtyEight().scrape_matches(year, league)
    
    @pytest.mark.parametrize(
        'year, league, expected',
        [(2015, 'All', pytest.raises(InvalidYearException)),
         ('a', 'Barclays Premier League', pytest.raises(ValueError)),
         ('All', 'German Bundesliga', does_not_raise())]
    )
    def test_invalid_year(self, year, league, expected):
        with expected:
            FiveThirtyEight().scrape_matches(year, league)
    
    @pytest.mark.parametrize(
        'year, league',
        [('All', 'All'), (2020, 'Spanish Primera Division'), (2017, 'German Bundesliga'),
         ('All', 'English League One'), (2023, 'All')]
    )
    def test_scrape_matches(self, year, league):
        df = FiveThirtyEight().scrape_matches(year, league)
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] > 0
        assert df.shape[1] > 0
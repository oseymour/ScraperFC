import sys
sys.path.append('./src/')
from ScraperFC import Capology
from ScraperFC.scraperfc_exceptions import InvalidYearException, InvalidLeagueException
from ScraperFC.utils import get_module_comps

import pytest
from contextlib import nullcontext as does_not_raise
import random
import pandas as pd

comps = get_module_comps("CAPOLOGY")

class TestCapology:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [(2017, 'England Premier League', pytest.raises(TypeError)),
         ('2020-21', 'Germany Bundesliga', does_not_raise()),
         ('2020-2021', 'Germany Bundesliga', pytest.raises(InvalidYearException))]
    )
    def test_invalid_year(self, year, league, expected):
        with expected:
            Capology().scrape_salaries(year, league, 'usd')

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('2021-22', 9, pytest.raises(TypeError)),
         ('2022-23', 'EPL', pytest.raises(InvalidLeagueException)),
         ('2022-23', 'Spain La Liga', does_not_raise())]
    )
    def test_invalid_league(self, year, league, expected):
        with expected:
            Capology().scrape_salaries(year, league, 'eur')

    # ==============================================================================================
    def test_scrape_salaries(self):
        capology = Capology()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(capology.get_valid_seasons(league), 1)[0]

        result = capology.scrape_salaries(year, league, 'gbp')
        assert type(result) is pd.DataFrame
        assert result.shape[0] > 0
        assert result.shape[1] > 0

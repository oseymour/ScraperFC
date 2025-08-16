import sys
import random
import pandas as pd
import pytest
from contextlib import nullcontext as does_not_raise
from rootutils import find_root

sys.path.append(str(find_root() / 'src'))
from ScraperFC import Transfermarkt
from ScraperFC.transfermarkt import comps
from ScraperFC.scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from ScraperFC.utils import get_module_comps

comps = get_module_comps("TRANSFERMARKT")

class TestTransfermarkt:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('23/24', 'England EFL League 2', does_not_raise()),
         (2024, 'Italy Serie A', pytest.raises(TypeError)),
         ('fake year', 'Italy Serie B', pytest.raises(InvalidYearException))]
    )
    def test_invalid_year(self, year, league, expected):
        tm = Transfermarkt()
        with expected:
            tm.get_club_links(year, league)
        with expected:
            tm.get_player_links(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('76/77', 'Spain La Liga', does_not_raise()),
         ('76/77', -1, pytest.raises(TypeError)),
         ('76/77', 'fake league', pytest.raises(InvalidLeagueException))]
    )
    def test_invalid_league(self, year, league, expected):
        tm = Transfermarkt()
        with expected:
            tm.get_valid_seasons(league)
        with expected:
            tm.get_club_links(year, league)
        with expected:
            tm.get_player_links(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        "year, league",
        [("1901/02", "Belgium Pro League"),]
    )
    def test_no_club_links(self, year, league):
        tm = Transfermarkt()
        with pytest.warns(UserWarning) as warning_info:
            club_links = tm.get_club_links(year, league)
        assert isinstance(club_links, list)
        assert len(club_links) == 0

    # ==============================================================================================
    def test_scrape_players(self):
        tm = Transfermarkt()
        league = random.sample(list(comps.keys()), 1)[0]
        valid_years = tm.get_valid_seasons(league)
        year = random.sample(list(valid_years.keys()), 1)[0]
        players = tm.scrape_players(year, league)
        assert type(players) is pd.DataFrame
        assert players.shape[0] > 0
        assert players.shape[1] > 0

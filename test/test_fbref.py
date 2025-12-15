import sys
import random
import numpy as np
import pandas as pd
import pytest

sys.path.append('./src/')
from ScraperFC import FBref
from ScraperFC.fbref import stats_categories
from ScraperFC.fbref_match import FBrefMatch
from ScraperFC.scraperfc_exceptions import NoMatchLinksException, InvalidLeagueException,\
    InvalidYearException
from ScraperFC.utils import get_module_comps

no_matches = {
    "Belgium Pro League": [
        "2003-2004", "2004-2005", "2005-2006", "2006-2007", "2007-2008", "2008-2009", "2009-2010",
        "2010-2011", "2011-2012", "2012-2013", "2013-2014",
    ],
    "France Ligue 2": ["2009-2010", "2010-2011", "2011-2012", "2012-2013", "2013-2014"],
    "Germany 2. Bundesliga": [
        "2003-2004", "2004-2005", "2005-2006", "2006-2007", "2007-2008", "2008-2009", "2009-2010",
        "2010-2011", "2011-2012", "2012-2013", "2013-2014"
    ],
    "Spain La Liga 2": [
        "2001-2002", "2002-2003", "2003-2004", "2004-2005", "2005-2006", "2006-2007", "2007-2008",
        "2008-2009", "2009-2010", "2010-2011", "2011-2012", "2012-2013", "2013-2014",
    ],
}

comps = get_module_comps("FBREF")


class TestFBref:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [
            (2021, 'Italy Serie B', pytest.raises(TypeError)),
            ('1642-1643', 'England Premier League', pytest.raises(InvalidYearException))
        ]
    )
    def test_invalid_year(self, year, league, expected):
        fbref = FBref()
        with expected:
            fbref.get_match_links(year, league)
        with expected:
            fbref.scrape_league_table(year, league)
        with expected:
            fbref.scrape_matches(year, league)
        with expected:
            fbref.scrape_stats(year, league, 'standard')
        with expected:
            fbref.scrape_all_stats(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [
            ('2018', (1, 2, 3), pytest.raises(TypeError)),
            ('2018', 'fake league', pytest.raises(InvalidLeagueException))
        ]
    )
    def test_invalid_league(self, year, league, expected):
        fbref = FBref()
        with expected:
            fbref.get_valid_seasons(league)
        with expected:
            fbref.get_match_links(year, league)
        with expected:
            fbref.scrape_league_table(year, league)
        with expected:
            fbref.scrape_matches(year, league)
        with expected:
            fbref.scrape_stats(year, league, 'standard')
        with expected:
            fbref.scrape_all_stats(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [
            ('2013-2014', 'France Ligue 2', pytest.raises(NoMatchLinksException)),
            ('2013-2014', 'Spain La Liga 2', pytest.raises(NoMatchLinksException)),
            ('2013-2014', 'Belgium Pro League', pytest.raises(NoMatchLinksException)),
        ]
    )
    def test_NoMatchLinksException(self, year, league, expected):
        fbref = FBref()
        with expected:
            fbref.get_match_links(year, league)
        with expected:
            fbref.scrape_matches(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected_len',
        [
            ('2020-2021', 'England Premier League', 380),
            ("2021", "UEFA European Championship", 51),
        ]
    )
    def test_valid_get_match_links(self, year, league, expected_len):
        fbref = FBref()
        match_links = fbref.get_match_links(year, league)
        assert type(match_links) is list, 'match links must be a list'
        assert np.all([type(x) is str for x in match_links])
        assert len(match_links) == expected_len, 'number of links does not match expected'

    # ==============================================================================================
    def test_scrape_league_table(self):
        fbref = FBref()
        league = random.sample(sorted(comps), 1)[0]
        year = random.sample(sorted(fbref.get_valid_seasons(league)), 1)[0]

        lg_table = fbref.scrape_league_table(year, league)
        assert type(lg_table) is list, 'league tables should be a list'
        assert np.all([type(x) is pd.DataFrame for x in lg_table]), 'all tables should be dataframes'

    # ==============================================================================================
    @pytest.mark.parametrize(
        "link",
        [
            "https://fbref.com/en/matches/2bc716a2/Columbus-Crew-LA-Galaxy-May-17-1998-Major-League-Soccer",  # Only has GK stats for 1 team, has scorebox_meta tag
            "https://fbref.com/en/matches/38293f32/Manchester-United-Aston-Villa-March-7-2021-Womens-Super-League",  # only has shots data for 1 team
            "https://fbref.com/en/matches/40e49e72/North-West-Derby-Liverpool-Manchester-United-May-5-2024-Womens-Super-League",  # No scorebox_meta tag
            "https://fbref.com/en/matches/bdbe67a7/Lanus-Chapecoense-May-17-2017-Copa-Libertadores",  # was awarded to one team
            "https://fbref.com/en/matches/ec86d292/Standard-Liege-Anderlecht-April-12-2019-Belgian-First-Division-A",  # was awarded to one team
            "https://fbref.com/en/matches/b787871d/Empoli-Hellas-Verona-August-19-2023-Serie-A",  # failed for someone on Discord, didn't find match date el
        ]
    )
    def test_scrape_specific_matches(self, link):
        fbref = FBref()
        _ = fbref.scrape_match(link)

    # ==============================================================================================
    def test_scrape_matches(self):
        fbref = FBref()
        league = random.sample(sorted(comps), 1)[0]
        year = random.sample(sorted(fbref.get_valid_seasons(league)), 1)[0]

        try:
            matches = fbref.scrape_matches(year, league)
            assert type(matches) is list
            assert np.all([type(m) is FBrefMatch for m in matches])
        except NoMatchLinksException:
            assert league in no_matches
            assert year in no_matches[league]

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, stat_category, expected',
        [('2023-2024', 'FBref Big 5 Combined', 'fake category', pytest.raises(ValueError))]
    )
    def test_fake_stat_category(self, year, league, stat_category, expected):
        fbref = FBref()

        with expected:
            fbref.scrape_stats(year, league, stat_category)

    # ==============================================================================================
    def test_scrape_all_stats(self):
        fbref = FBref()
        league = random.sample(sorted(comps), 1)[0]
        year = random.sample(sorted(fbref.get_valid_seasons(league)), 1)[0]

        stats = fbref.scrape_all_stats(year, league)

        assert type(stats) is dict
        for key, value in stats.items():
            assert key in stats_categories.keys()
            assert type(value) is dict
            assert "squad" in value
            assert "opponent" in value
            assert "player" in value
            assert type(value["squad"]) is pd.DataFrame
            assert type(value["opponent"]) is pd.DataFrame
            assert type(value["player"]) is pd.DataFrame

    # ==============================================================================================
    @pytest.mark.parametrize(
        "year, league",
        [
            ("1954-1955", "England Premier League"),  # doesn't have any stat categories data
            ("2024-2025", "UEFA Champions League"),  # should be "normal"
            ("2024-2025", "FBref Big 5 Combined"),  # cuz it's different
        ]
    )
    def test_scrape_specific_all_stats(self, year, league):
        fbref = FBref()
        stats = fbref.scrape_all_stats(year, league)
        assert type(stats) is dict
        for key, value in stats.items():
            assert key in stats_categories.keys()
            assert type(value) is dict
            assert "squad" in value
            assert "opponent" in value
            assert "player" in value
            assert type(value["squad"]) is pd.DataFrame
            assert type(value["opponent"]) is pd.DataFrame
            assert type(value["player"]) is pd.DataFrame

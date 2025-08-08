import sys
sys.path.append('./src/')
from ScraperFC import FBref
from ScraperFC.fbref import comps, stats_categories
from ScraperFC.scraperfc_exceptions import NoMatchLinksException, InvalidLeagueException,\
    InvalidYearException

import random
import numpy as np
import pandas as pd
import pytest

# These leagues and years do not have match links on FBref
comps_wo_matches = [
    ('2009-2010', 'Ligue 2'), ('2010-2011', 'Ligue 2'), ('2011-2012', 'Ligue 2'),
    ('2012-2013', 'Ligue 2'), ('2013-2014', 'Ligue 2'),
    ('2013-2014', 'La Liga 2'), ('2012-2013', 'La Liga 2'), ('2011-2012', 'La Liga 2'),
    ('2010-2011', 'La Liga 2'), ('2009-2010', 'La Liga 2'), ('2008-2009', 'La Liga 2'),
    ('2007-2008', 'La Liga 2'), ('2006-2007', 'La Liga 2'), ('2005-2006', 'La Liga 2'),
    ('2004-2005', 'La Liga 2'), ('2003-2004', 'La Liga 2'), ('2002-2003', 'La Liga 2'),
    ('2001-2002', 'La Liga 2'),
    ('2003-2004', 'Belgian Pro League'), ('2004-2005', 'Belgian Pro League'),
    ('2005-2006', 'Belgian Pro League'), ('2006-2007', 'Belgian Pro League'),
    ('2007-2008', 'Belgian Pro League'), ('2008-2009', 'Belgian Pro League'),
    ('2009-2010', 'Belgian Pro League'), ('2010-2011', 'Belgian Pro League'),
    ('2011-2012', 'Belgian Pro League'), ('2012-2013', 'Belgian Pro League'),
    ('2013-2014', 'Belgian Pro League'),
    ("2003-2004", "2. Bundesliga"), ("2004-2005", "2. Bundesliga"), ("2005-2006", "2. Bundesliga"),
    ("2006-2007", "2. Bundesliga"), ("2007-2008", "2. Bundesliga"), ("2008-2009", "2. Bundesliga"),
    ("2009-2010", "2. Bundesliga"), ("2010-2011", "2. Bundesliga"), ("2011-2012", "2. Bundesliga"),
    ("2012-2013", "2. Bundesliga"), ("2013-2014", "2. Bundesliga"),
]


class TestFBref:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [(2021, 'Serie B', pytest.raises(TypeError)),
         ('1642-1643', 'EPL', pytest.raises(InvalidYearException))]
    )
    def test_invalid_year(self, year, league, expected):
        fbref = FBref()
        with expected:
            fbref.get_season_link(year, league)
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
        [('2018', (1, 2, 3), pytest.raises(TypeError)),
         ('2018', 'fake comp', pytest.raises(InvalidLeagueException))]
    )
    def test_invalid_league(self, year, league, expected):
        fbref = FBref()
        with expected:
            fbref.get_valid_seasons(league)
        with expected:
            fbref.get_season_link(year, league)
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
        [('2013-2014', 'Ligue 2', pytest.raises(NoMatchLinksException)),
         ('2013-2014', 'La Liga 2', pytest.raises(NoMatchLinksException)),
         ('2013-2014', 'Belgian Pro League', pytest.raises(NoMatchLinksException)),]
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
        [('2020-2021', 'EPL', 380)]
    )
    def test_valid_get_match_links(self, year, league, expected_len):
        fbref = FBref()
        # league = random.sample(list(comps.keys()), 1)[0]
        # year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]

        match_links = fbref.get_match_links(year, league)
        assert type(match_links) is list, 'match links must be a list'
        assert np.all([type(x) is str for x in match_links])
        assert len(match_links) == expected_len, 'number of links does not match expected'

    # ==============================================================================================
    def test_scrape_league_table(self):
        fbref = FBref()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]

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
        ]
    )
    def test_scrape_specific_matches(self, link):
        fbref = FBref()
        _ = fbref.scrape_match(link)

    # ==============================================================================================
    def test_scrape_matches(self):
        fbref = FBref()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]

        try:
            matches = fbref.scrape_matches(year, league)
            assert type(matches) is pd.DataFrame, 'matches must be a dataframe'
            assert matches.shape[0] > 0
            assert matches.shape[1] > 0
        except NoMatchLinksException:
            # assert ((year, league) in comps_wo_matches) or (league == "Big 5 combined")
            pass

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, stat_category, expected',
        [('2023-2024', 'Big 5 combined', 'fake category', pytest.raises(ValueError))]
    )
    def test_fake_stat_category(self, year, league, stat_category, expected):
        fbref = FBref()

        with expected:
            fbref.scrape_stats(year, league, stat_category)

    # ==============================================================================================
    def test_scrape_all_stats(self):
        fbref = FBref()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
        print(f"Testing scrape_all_stats for {year}, {league}.")

        with pytest.warns(UserWarning):
            stats = fbref.scrape_all_stats(year, league)
            assert type(stats) is tuple
            assert not stats[0]




        assert type(stats) is dict
        for key, value in stats.items():
            assert key in stats_categories.keys()
            assert type(value) is tuple
            assert len(value) == 3
            assert type(value[0]) is pd.DataFrame or value[0] is None
            assert type(value[1]) is pd.DataFrame or value[1] is None
            assert type(value[2]) is pd.DataFrame or value[2] is None

    # ==============================================================================================
    @pytest.mark.parametrize(
        "year, league",
        [
            ("1954-1955", "EPL"),  # doesn't have any stat categories data
            ("2024-2025", "Champions League"),  # should be "normal"
            ("2024-2025", "Big 5 combined"),  # cuz it's different
        ]
    )
    def test_scrape_specific_all_stats(self, year, league):
        fbref = FBref()
        stats = fbref.scrape_all_stats(year, league)
        assert type(stats) is dict
        for key, value in stats.items():
            assert key in stats_categories.keys()
            assert type(value) is tuple
            assert len(value) == 3
            assert type(value[0]) is pd.DataFrame or value[0] is None
            assert type(value[1]) is pd.DataFrame or value[1] is None
            assert type(value[2]) is pd.DataFrame or value[2] is None

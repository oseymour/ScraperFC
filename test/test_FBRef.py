import sys
sys.path.append('./src/')
from ScraperFC import FBRef
from ScraperFC.FBRef import comps, stats_categories
from ScraperFC.scraperfc_exceptions import (
    NoMatchLinksException, InvalidLeagueException, InvalidYearException)
import random
import numpy as np
import pandas as pd
import pytest
from contextlib import nullcontext as does_not_raise

# These leagues and years do not have match links on FBRef
comps_wo_matches = [
    ('2009-2010', 'Ligue 2'), ('2010-2011', 'Ligue 2'), ('2011-2012', 'Ligue 2'), 
    ('2012-2013', 'Ligue 2'), ('2013-2014', 'Ligue 2'), ('2013-2014', 'La Liga 2'),
    ('2012-2013', 'La Liga 2'), ('2011-2012', 'La Liga 2'), ('2010-2011', 'La Liga 2'),
    ('2009-2010', 'La Liga 2'), ('2008-2009', 'La Liga 2'), ('2007-2008', 'La Liga 2'),
    ('2006-2007', 'La Liga 2'), ('2005-2006', 'La Liga 2'), ('2004-2005', 'La Liga 2'),
    ('2003-2004', 'La Liga 2'), ('2002-2003', 'La Liga 2'), ('2001-2002', 'La Liga 2'),
    ('2003-2004', 'Belgian Pro League'), ('2004-2005', 'Belgian Pro League'),
    ('2005-2006', 'Belgian Pro League'), ('2006-2007', 'Belgian Pro League'),
    ('2007-2008', 'Belgian Pro League'), ('2008-2009', 'Belgian Pro League'),
    ('2009-2010', 'Belgian Pro League'), ('2010-2011', 'Belgian Pro League'),
    ('2011-2012', 'Belgian Pro League'), ('2012-2013', 'Belgian Pro League'),
    ('2013-2014', 'Belgian Pro League')]


# class TestFBRef:

    # # ==============================================================================================
    # @pytest.mark.parametrize(
    #     'year, league, expected',
    #     [(2021, 'Serie B', pytest.raises(TypeError)),
    #      ('1642-1643', 'EPL', pytest.raises(InvalidYearException))])
    # def test_invalid_year(self, year, league, expected):
    #     fbref = FBRef()
    #     print(year, league)
    #     with expected:
    #         print('Testing get_season_link')
    #         fbref.get_season_link(year, league)
    #     with expected:
    #         print('Testing get_match_links')
    #         fbref.get_match_links(year, league)
    #     with expected:
    #         print('Testing scrape_league_table')
    #         fbref.scrape_league_table(year, league)
    #     with expected:
    #         print('Testing scrape_matches')
    #         fbref.scrape_matches(year, league)
    #     with expected:
    #         print('Testing scrape_stats')
    #         fbref.scrape_stats(year, league, 'standard')
    #     with expected:
    #         print('Testing scrape_all_stats')
    #         fbref.scrape_all_stats(year, league)

    # # ==============================================================================================
    # @pytest.mark.parametrize(
    #     'year, league, expected',
    #     [('2018', (1, 2, 3), pytest.raises(TypeError)),
    #      ('2018', 'fake comp', pytest.raises(InvalidLeagueException))])
    # def test_invalid_league(self, year, league, expected):
    #     fbref = FBRef()
    #     print(year, league)
    #     with expected:
    #         print('Testing get_valid_seasons')
    #         fbref.get_valid_seasons(league)
    #     with expected:
    #         print('Testing get_season_link')
    #         fbref.get_season_link(year, league)
    #     with expected:
    #         print('Testing get_match_links')
    #         fbref.get_match_links(year, league)
    #     with expected:
    #         print('Testing scrape_league_table')
    #         fbref.scrape_league_table(year, league)
    #     with expected:
    #         print('Testing scrape_matches')
    #         fbref.scrape_matches(year, league)
    #     with expected:
    #         print('Testing scrape_stats')
    #         fbref.scrape_stats(year, league, 'standard')
    #     with expected:
    #         print('Testing scrape_all_stats')
    #         fbref.scrape_all_stats(year, league)

    # # ==============================================================================================
    # @pytest.mark.parametrize(
    #     'year, league, expected',
    #     [('2013-2014', 'Ligue 2', pytest.raises(NoMatchLinksException)),
    #      ('2013-2014', 'La Liga 2', pytest.raises(NoMatchLinksException)),
    #      ('2013-2014', 'Belgian Pro League', pytest.raises(NoMatchLinksException)),])
    # def test_NoMatchLinksException(self, year, league, expected):
    #     fbref = FBRef()
    #     print(year, league)
    #     with expected:
    #         fbref.get_match_links(year, league)
    #     with expected:
    #         fbref.scrape_matches(year, league)

    # # ==============================================================================================
    # @pytest.mark.parametrize(
    #     'year, league, expected_len',
    #     [('2020-2021', 'EPL', 380)])
    # def test_valid_get_match_links(self, year, league, expected_len):
    #     fbref = FBRef()
    #     # league = random.sample(list(comps.keys()), 1)[0]
    #     # year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
    #     print(year, league)
    #     match_links = fbref.get_match_links(year, league)
    #     assert type(match_links) is list, 'match links must be a list'
    #     assert (np.all([type(x) is str for x in match_links]), 
    #             'all of the match links should be strings')
    #     assert len(match_links) == expected_len, 'number of links does not match expected'

    # # ==============================================================================================
    # def test_scrape_league_table(self):
    #     fbref = FBRef()
    #     league = random.sample(list(comps.keys()), 1)[0]
    #     year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
    #     print(year, league)
    #     lg_table = fbref.scrape_league_table(year, league)
    #     assert type(lg_table) is list, 'league tables should be a list'
    #     assert np.all([type(x) is pd.DataFrame for x in lg_table]), 'all tables should be dataframes'

    # # ============================================================================================
    # def test_scrape_matches(self):
    #     fbref = FBRef()
    #     league = random.sample(list(comps.keys()), 1)[0]
    #     year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
    #     print(year, league)
    #     try:
    #         matches = fbref.scrape_matches(year, league)
    #         assert type(matches) is pd.DataFrame, 'matches must be a dataframe'
    #         assert matches.shape[0] > 0, 'matches must have more than 1 row'
    #     except NoMatchLinksException:
    #         assert (year, league) in comps_wo_matches

    # # ==============================================================================================
    # @pytest.mark.parametrize(
    #     'year, league, stat_category, expected',
    #     [('2023-2024', 'Big 5 combined', 'fake category', pytest.raises(ValueError))])
    # def test_fake_stat_category(self, year, league, stat_category, expected):
    #     fbref = FBRef()
    #     print(year, league, stat_category)
    #     with expected:
    #         fbref.scrape_stats(year, league, stat_category)

    # # ============================================================================================
    # def test_scrape_all_stats(self):
    #     fbref = FBRef()
    #     league = random.sample(list(comps.keys()), 1)[0]
    #     year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
    #     print(year, league)
    #     stats = fbref.scrape_all_stats(year, league)
    #     assert type(stats) is dict
    #     for key, value in stats.items():
    #         assert key in stats_categories.keys()
    #         assert type(value) is tuple
    #         assert len(value) == 3
    #         assert type(value[0]) is pd.DataFrame or value[0] is None
    #         assert type(value[1]) is pd.DataFrame or value[1] is None
    #         assert type(value[2]) is pd.DataFrame or value[2] is None

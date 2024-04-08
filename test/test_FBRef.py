import sys
sys.path.append('./src/')
from ScraperFC import FBRef
from ScraperFC.FBRef import comps
import random
import numpy as np
import pandas as pd

class TestFBRef:

    def test_get_match_links(self):
        fbref = FBRef()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
        print(year, league)
        match_links = fbref.get_match_links(year, league)
        assert type(match_links) is list, 'match links must be a list'
        assert np.all([type(x) is str for x in match_links]), 'all of the match links should be strings'
        assert len(match_links) > 0, 'there should be more than 0 match links'

    def test_scrape_league_table(self):
        fbref = FBRef()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
        print(year, league)
        lg_table = fbref.scrape_league_table(year, league)
        assert type(lg_table) is list, 'league tables should be a list'
        assert np.all([type(x) is pd.DataFrame for x in lg_table]), 'all tables should be dataframes'

    def test_scrape_matches(self):
        fbref = FBRef()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(fbref.get_valid_seasons(league).keys()), 1)[0]
        print(year, league)
        matches = fbref.scrape_matches(year, league)
        assert type(matches) is pd.DataFrame, 'matches must be a dataframe'
        assert matches.shape[0] > 0, 'matches must have more than 1 row'


    
    # def test_get_season_link(self):
    #     year, league = get_random_league_seasons('FBRef', 1)[0]
    #     try:
    #         fbref = FBRef()
    #         season_link = fbref.get_season_link(year, league)
    #         assert type(season_link) is str
    #     except UnavailableSeasonException:
    #         pass
    #     finally:
    #         fbref.close()

    # def test_scrape_all_stats_unnormalized(self):
    #     year, league = get_random_league_seasons('FBRef', 1)[0]
    #     try:
    #         fbref = FBRef()
    #         stats = fbref.scrape_all_stats(year, league)
    #         assert type(stats) == dict
    #         for key, value in stats.items():
    #             assert key in fbref.stats_categories.keys()
    #             assert type(value) is tuple
    #             assert len(value) == 3
    #             assert type(value[0]) is DataFrame or value[0] is None
    #             assert type(value[1]) is DataFrame or value[1] is None
    #             assert type(value[2]) is DataFrame or value[2] is None
    #     except UnavailableSeasonException:
    #         pass
    #     finally:
    #         fbref.close()

    # def test_scrape_all_stats_normalized(self):
    #     year, league = get_random_league_seasons('FBRef', 1)[0]
    #     print(year, league)
    #     try:
    #         fbref = FBRef()
    #         stats = fbref.scrape_all_stats(year, league, normalize=True)
    #         assert type(stats) == dict
    #         for key, value in stats.items():
    #             assert key in fbref.stats_categories.keys()
    #             assert type(value) is DataFrame
    #     except UnavailableSeasonException:
    #         pass
    #     finally:
    #         fbref.close()

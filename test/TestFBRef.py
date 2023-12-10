import sys
sys.path.append('../')
from ScraperFC import FBRef, get_source_comp_info, NoMatchLinksException, \
    UnavailableSeasonException
from shared_test_functions import get_random_league_seasons
import random
from pandas import DataFrame

class TestFBRef:

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

    # def test_get_match_links_type(self):
    #     year, league = get_random_league_seasons('FBRef', 1)[0]
    #     try:
    #         fbref = FBRef()
    #         match_links = fbref.get_match_links(year, league)
    #         assert type(match_links) is list
    #     except (NoMatchLinksException, UnavailableSeasonException):
    #         pass
    #     finally:
    #         fbref.close()

    # def test_get_match_link_contents(self):
    #     year, league = get_random_league_seasons('FBRef', 1)[0]
    #     try:
    #         fbref = FBRef()
    #         match_links = fbref.get_match_links(year, league)
    #         link = random.sample(match_links, 1)[0]
    #         finder = get_source_comp_info(year, league, 'FBRef')['FBRef'][league]['finder']
    #         assert type(link) is str
    #         if type(finder) is list:
    #             for f in finder:
    #                 assert f in link
    #         else:
    #             assert finder in link
    #         assert 'fbref.com' in link
    #     except (NoMatchLinksException, UnavailableSeasonException):
    #         pass
    #     finally:
    #         fbref.close()

    # def test_scrape_league_table(self):
    #     year, league = get_random_league_seasons('FBRef', 1)[0]
    #     try:
    #         fbref = FBRef()
    #         lgtbl = fbref.scrape_league_table(year, league)
    #         assert type(lgtbl) in (list, DataFrame)
    #         if type(lgtbl) is list:
    #             for x in lgtbl:
    #                 assert type(x) is DataFrame
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

    def test_scrape_matches(self):
        year, league = get_random_league_seasons('FBRef', 1)[0]
        try:
            fbref = FBRef()
            matches = fbref.scrape_matches(year, league)
            assert type(matches) is DataFrame
            assert matches.shape[0] > 0
        except UnavailableSeasonException:
            pass
        finally:
            fbref.close()

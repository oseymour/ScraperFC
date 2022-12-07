import sys
sys.path.insert(0, '..') # import local ScraperFC, not pypi installed version
import ScraperFC as sfc
from ScraperFC import sources, InvalidYearException, UnavailableSeasonException, NoMatchLinksException
import numpy as np
import itertools
import datetime # DO NOT import datetime as datetime, need to check type datetime.date, not datetime.datetime.date
import pandas as pd
from tqdm import tqdm
import traceback


leagues = sources["FBRef"].keys()
years = range(1988, datetime.datetime.now().year+1)
iterator = list(itertools.product(leagues, years))

########################################################################################################################
def get_random_league_season():
    got_random = False
    try:
        scraper = sfc.FBRef()
        while not got_random:
            random_idx = np.random.choice(len(iterator), size=1, replace=False)[0]
            league, year = np.array(iterator)[random_idx]
            league, year = str(league), int(year)
            try:
                sfc.shared_functions.check_season(year,league,'FBRef')
                scraper.get_match_links(year, league)
                got_random = True
            except:
                pass
    finally:
        scraper.close()

    return year, league


########################################################################################################################
class TestFBRef:

    ####################################################################################################################
    def test_scrape_match(self):
        print('Testing FBRef scrape_match().')
        scraper = sfc.FBRef()
        try:
            # Randomly pick year/league combos until a valid one
            year, league = get_random_league_season()
            print(year, league)
            match_links = scraper.get_match_links(year, league)
            link = list(match_links)[len(match_links)//2]
            print(link)
            match = scraper.scrape_match(link)

            player_stats_columns = [
                'Team Sheet', 'Summary', 'GK', 'Passing', 'Pass Types', 'Defense', 'Possession', 'Misc'
            ]
            assert type(match['Link'].values[0]) is str
            assert type(match['Date'].values[0]) is datetime.date
            assert type(match['Stage'].values[0]) in [int, str]
            assert type(match['Home Team'].values[0]) is str
            assert type(match['Away Team'].values[0]) is str
            assert type(match['Home Team ID'].values[0]) is str
            assert type(match['Away Team ID'].values[0]) is str
            assert type(match['Home Formation'].values[0]) in [type(None), str]
            assert type(match['Away Formation'].values[0]) in [type(None), str]
            assert type(match['Home Goals'].values[0]) is int
            assert type(match['Away Goals'].values[0]) is int
            assert type(match['Home Ast'].values[0]) is int or np.isnan(match['Home Ast'].values[0])
            assert type(match['Away Ast'].values[0]) is int or np.isnan(match['Away Ast'].values[0])

            assert type(match['Home xG'].values[0]) in [type(None), float]
            assert type(match['Away xG'].values[0]) in [type(None), float]
            assert type(match['Home npxG'].values[0]) in [type(None), float]
            assert type(match['Away npxG'].values[0]) in [type(None), float]
            assert type(match['Home xAG'].values[0]) in [type(None), float]
            assert type(match['Away xAG'].values[0]) in [type(None), float]
        
            assert type(match['Home Player Stats'].values[0]) is pd.core.frame.DataFrame
            assert list(match['Home Player Stats'].values[0].columns) == player_stats_columns
            for c in match['Home Player Stats'].values[0].columns:
                stat_type = type(match['Home Player Stats'].values[0][c].values[0])
                assert stat_type in [type(None), pd.core.frame.DataFrame]
            
            assert type(match['Away Player Stats'].values[0]) is pd.core.frame.DataFrame
            assert list(match['Away Player Stats'].values[0].columns) == player_stats_columns
            for c in match['Away Player Stats'].values[0].columns:
                stat_type = type(match['Away Player Stats'].values[0][c].values[0])
                assert stat_type in [type(None), pd.core.frame.DataFrame]
            
            assert type(match['Shots'].values[0]) is pd.core.frame.DataFrame
            assert list(match['Shots'].values[0].columns) == ['Both', 'Home', 'Away']
            for c in match['Shots'].values[0].columns:
                stat_type = type(match['Shots'].values[0][c].values[0])
                assert stat_type in [type(None), pd.core.frame.DataFrame]
        finally:
            scraper.close()

    ####################################################################################################################
    def test_scrape_matches(self):
        print('Testing FBRef scrape_matches().')
        scraper = sfc.FBRef()
        try:
            # Randomly pick year/league combos until a valid one
            year, league = get_random_league_season()

            match_links = scraper.get_match_links(year, league)
            matches = scraper.scrape_matches(year, league)

            assert matches.shape[0] == len(match_links)
        finally:
            scraper.close()

    ####################################################################################################################
    def test_scrape_all_stats(self):
        print('Testing FBRef scrape_all_stats().')
        scraper = sfc.FBRef()
        try:
            # Randomly pick year/league combos until a valid one
            year, league = get_random_league_season()
   
            stats = scraper.scrape_all_stats(year=year, league=league)
            stats_categories = scraper.stats_categories.keys()

            for category in stats_categories:
                assert len(stats[category]) == 3
                squad, opponent, player = stats[category]

                if squad is not None:
                    pass

                if opponent is not None:
                    pass

                if player is not None:
                    pass
        finally:
            scraper.close()

    ####################################################################################################################
    def test_sources(self):
        print('Testing FBRef sources.')
        scraper = sfc.FBRef()
        try:
            for (league, year) in tqdm(iterator):
                year = int(year) # year became a string during random sampling?
                league = str(league) # league also became a weird type of numpy string?
                print(year, league)

                # Skip invalid years
                try:
                    sfc.shared_functions.check_season(year, league, "FBRef")
                except InvalidYearException:
                    continue

                try:
                    season_link = scraper.get_season_link(year, league)
                except UnavailableSeasonException:
                    continue

                try:
                    match_links = scraper.get_match_links(year, league)
                except NoMatchLinksException:
                    continue

                assert type(season_link) is str

                assert len(match_links) > 0
        finally:
            scraper.close()

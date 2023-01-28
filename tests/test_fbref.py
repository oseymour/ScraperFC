import sys
sys.path.insert(0, '..') # import local ScraperFC, not pypi installed version
import ScraperFC as sfc
import numpy as np
import itertools
import datetime # DO NOT import datetime as datetime, need to check type datetime.date, not datetime.datetime.date
import pandas as pd
from tqdm import tqdm
import traceback
from shared_test_functions import get_random_league_seasons


########################################################################################################################
class TestFBRef:

    ####################################################################################################################
    def verify_match_df(self, match):
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

    ####################################################################################################################
    def verify_matches_df(self, matches, match_links):
        assert matches.shape[0] == len(match_links)
        for i in matches.index:
            self.verify_match_df(matches.loc[i,:])

    ####################################################################################################################
    def verify_all_stats(self, stats):
        scraper = sfc.FBRef()
        try:
            stats_categories = scraper.stats_categories.keys()

            assert len(stats.keys()) == len(stats_categories)

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
    def test_fbref(self):
        print('Testing FBRef sources.')
        scraper = sfc.FBRef()
        try:
            iterator = get_random_league_seasons('FBRef', 'all')
            for league, year in tqdm(iterator):
                # year = int(year) # year became a string during random sampling?
                # league = str(league) # league also became a weird type of numpy string?
                print(year, league)

                # Skip invalid years -----------------------------------------------------------------------------------
                try:
                    sfc.shared_functions.check_season(year, league, 'FBRef')
                except sfc.InvalidYearException:
                    continue

                # Season link ------------------------------------------------------------------------------------------
                try:
                    season_link = scraper.get_season_link(year, league)
                except sfc.UnavailableSeasonException:
                    continue
                assert type(season_link) is str

                # Match links ------------------------------------------------------------------------------------------
                try:
                    match_links = scraper.get_match_links(year, league)
                except sfc.NoMatchLinksException:
                    continue
                assert len(match_links) > 0

                # Get match data and stats -----------------------------------------------------------------------------
                matches = scraper.scrape_matches(year, league)
                stats= scraper.scrape_all_stats(year, league)

                # Check match data and stats ---------------------------------------------------------------------------
                self.verify_all_stats(stats)
                self.verify_matches_df(matches, match_links)
        finally:
            scraper.close()

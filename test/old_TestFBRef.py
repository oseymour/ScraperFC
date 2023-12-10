import sys
sys.path.insert(0, '..') # import local ScraperFC, not pypi installed version
import ScraperFC as sfc
import numpy as np
import itertools
import datetime # DO NOT import datetime as datetime, need to check type datetime.date, not datetime.datetime.date
import pandas as pd
from tqdm.auto import tqdm
import traceback
from shared_test_functions import get_random_league_seasons


########################################################################################################################
class TestFBRef:

    ####################################################################################################################
    def verify_match_df(self, match):
        player_stats_columns = [
            'Team Sheet', 'Summary', 'GK', 'Passing', 'Pass Types', 'Defense', 'Possession', 'Misc'
        ]
        assert type(match['Link']) is str
        assert type(match['Date']) is datetime.date
        assert type(match['Stage']) in [int, str]
        assert type(match['Home Team']) is str
        assert type(match['Away Team']) is str
        assert type(match['Home Team ID']) is str
        assert type(match['Away Team ID']) is str
        assert type(match['Home Formation']) in [type(None), str]
        assert type(match['Away Formation']) in [type(None), str]
        assert type(match['Home Goals']) is int
        assert type(match['Away Goals']) is int
        assert type(match['Home Ast']) is int or np.isnan(match['Home Ast'])
        assert type(match['Away Ast']) is int or np.isnan(match['Away Ast'])

        assert type(match['Home xG']) in [type(None), float]
        assert type(match['Away xG']) in [type(None), float]
        assert type(match['Home npxG']) in [type(None), float]
        assert type(match['Away npxG']) in [type(None), float]
        assert type(match['Home xAG']) in [type(None), float]
        assert type(match['Away xAG']) in [type(None), float]
    
        assert type(match['Home Player Stats']) is pd.core.frame.DataFrame
        assert list(match['Home Player Stats'].columns) == player_stats_columns
        for c in match['Home Player Stats'].columns:
            stat_type = type(match['Home Player Stats'][c].values[0])
            assert stat_type in [type(None), pd.core.frame.DataFrame]
        
        assert type(match['Away Player Stats']) is pd.core.frame.DataFrame
        assert list(match['Away Player Stats'].columns) == player_stats_columns
        for c in match['Away Player Stats'].columns:
            stat_type = type(match['Away Player Stats'][c].values[0])
            assert stat_type in [type(None), pd.core.frame.DataFrame]
        
        assert type(match['Shots']) is pd.core.frame.DataFrame
        assert list(match['Shots'].columns) == ['Both', 'Home', 'Away']
        for c in match['Shots'].columns:
            stat_type = type(match['Shots'][c].values[0])
            assert stat_type in [type(None), pd.core.frame.DataFrame]

    ####################################################################################################################
    def verify_matches_df(self, matches, match_links):
        assert matches.shape[0] == len(match_links)
        for i in matches.index:
            self.verify_match_df(matches.loc[i,:])

    ####################################################################################################################
    def verify_all_stats(self, stats):
        fbref = sfc.FBRef()
        try:
            stats_categories = fbref.stats_categories.keys()

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
            fbref.close()

    ####################################################################################################################
    def test_fbref(self):
        print('Testing FBRef.')
        fbref = sfc.FBRef()
        try:
            iterator = tqdm(get_random_league_seasons('FBRef', 'all'), desc='TestFBRef')
            for league, year in iterator:
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
                    season_link = fbref.get_season_link(year, league)
                except sfc.UnavailableSeasonException:
                    continue
                assert type(season_link) is str

                # Match links ------------------------------------------------------------------------------------------
#                 try:
                match_links = fbref.get_match_links(year, league)
#                 except sfc.NoMatchLinksException:
#                     continue
                assert len(match_links) > 0

                # Get match data and stats -----------------------------------------------------------------------------
                matches = fbref.scrape_matches(year, league)
                stats = fbref.scrape_all_stats(year, league)

                # Check match data and stats ---------------------------------------------------------------------------
                self.verify_all_stats(stats)
                self.verify_matches_df(matches, match_links)
        finally:
            fbref.close()

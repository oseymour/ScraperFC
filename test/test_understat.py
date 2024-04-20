import sys
sys.path.append('./src/')
from ScraperFC import Understat
from ScraperFC.Understat import comps
import random
import pandas as pd

class TestUnderstat:

    # # ==============================================================================================
    # def test_invalid_year(self, year, league, expected):
    #     raise NotImplementedError
    
    # # ==============================================================================================
    # def test_invalid_league(self, year, league, expected):
    #     raise NotImplementedError
    
    # ==============================================================================================
    def test_scrape_matches(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            matches = understat.scrape_matches(year, league)
            assert type(matches) is pd.DataFrame
            assert matches.shape[0] > 0
            assert matches.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_league_table(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            matches = understat.scrape_league_table(year, league)
            assert type(matches) is pd.DataFrame
            assert matches.shape[0] > 0
            assert matches.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_home_away_tables(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            table = understat.scrape_home_away_tables(year, league)
            assert type(table) is tuple
            for x in table:
                assert type(x) is pd.DataFrame
                assert x.shape[0] > 0
                assert x.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_situations(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            game_states = understat.scrape_situations(year, league)
            assert type(game_states) is pd.DataFrame
            assert game_states.shape[0] > 0
            assert game_states.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_formations(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            situations = understat.scrape_formations(year, league)
            assert type(situations) is dict
            for value in situations.values():
                assert type(value) is dict
                for value2 in value.values():
                    assert type(value2) is pd.Series
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_game_states(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            game_states = understat.scrape_game_states(year, league)
            assert type(game_states) is pd.DataFrame
            assert game_states.shape[0] > 0
            assert game_states.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_timing(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            game_states = understat.scrape_timing(year, league)
            assert type(game_states) is pd.DataFrame
            assert game_states.shape[0] > 0
            assert game_states.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_shot_zones(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            shot_zones = understat.scrape_shot_zones(year, league)
            assert type(shot_zones) is pd.DataFrame
            assert shot_zones.shape[0] > 0
            assert shot_zones.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_attack_speeds(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            attack_speeds = understat.scrape_attack_speeds(year, league)
            assert type(attack_speeds) is pd.DataFrame
            assert attack_speeds.shape[0] > 0
            assert attack_speeds.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_shot_results(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            shots = understat.scrape_shot_results(year, league)
            assert type(shots) is pd.DataFrame
            assert shots.shape[0] > 0
            assert shots.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_shot_xy_df(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            xy = understat.scrape_shot_xy(year, league, as_df=True)
            assert type(xy) is pd.DataFrame
            assert xy.shape[0] > 0
            assert xy.shape[1] > 0
        finally:
            understat.close()

    # ==============================================================================================
    def test_scrape_shot_xy_dict(self):
        understat = Understat()
        try:
            league = random.sample(list(comps.keys()), 1)[0]
            year = random.sample(list(understat.get_valid_seasons(league)), 1)[0]
            xy = understat.scrape_shot_xy(year, league, as_df=False)
            assert type(xy) is dict
            for value in xy.values():
                assert type(value) is dict
                assert list(value.keys()) == ['h', 'a']
                for value2 in value.values():
                    assert type(value2) is list
                    for x in value2:
                        assert type(x) is dict
        finally:
            understat.close()

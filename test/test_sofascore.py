import sys
sys.path.append('./src/')
from ScraperFC import Sofascore
from ScraperFC.scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from ScraperFC.sofascore import comps

import pytest
from contextlib import nullcontext as does_not_raise
import random
import numpy as np
import pandas as pd

match_url = 'https://www.sofascore.com/fc-bayern-munchen-manchester-united/Ksxdb#id:11605966'
match_id = 11605966

class TestSofascore:

    # ==============================================================================================
    @pytest.mark.parametrize(
        'match, expected',
        [(match_url, does_not_raise()),
         (match_id, does_not_raise()),
         (112.0, pytest.raises(TypeError)),
         ((match_url,), pytest.raises(TypeError)),
         ([match_id,], pytest.raises(TypeError))]
    )
    def test_match_url_vs_id(self, match, expected):
        """ Test that functions that take in match URLs or match IDs can actually take both.
        """
        ss = Sofascore()
        with expected:
            ss.get_match_dict(match)
        with expected:
            ss.get_team_names(match)
        with expected:
            ss.get_player_ids(match)
        with expected:
            ss.scrape_match_momentum(match)
        with expected:
            ss.scrape_team_match_stats(match)
        with expected:
            ss.scrape_player_match_stats(match)
        with expected:
            ss.scrape_player_average_positions(match)
        with expected:
            ss.scrape_heatmaps(match)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('19/20', 'Ligue 1', does_not_raise()),
         ('23/24', 'fake league', pytest.raises(InvalidLeagueException)),
         ('17/18', 2000, pytest.raises(TypeError))]
    )
    def test_invalid_leagues(self, year, league, expected):
        """ Test checks on league input
        """
        ss = Sofascore()
        with expected:
            ss.get_valid_seasons(league)
        with expected:
            ss.get_match_dicts(year, league)
        with expected:
            ss.scrape_player_league_stats(year, league)

    # ==============================================================================================
    @pytest.mark.parametrize(
        'year, league, expected',
        [('17/18', 'La Liga', does_not_raise()),
         ('fake year', 'EPL', pytest.raises(InvalidYearException)),
         (2024, 'EPL', pytest.raises(TypeError))]
    )
    def test_invalid_years(self, year, league, expected):
        """ Test checks on year input
        """
        ss = Sofascore()
        with expected:
            ss.get_match_dicts(year, league)
        with expected:
            ss.scrape_player_league_stats(year, league)

    # ==============================================================================================
    def test_get_match_dicts(self):
        """ Test the outputs of the get_match_dicts() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        assert isinstance(match_dicts, list)
        assert np.all([isinstance(x, dict) for x in match_dicts])

    # ==============================================================================================
    def test_get_match_dict(self):
        """ Test the outputs of the get_match_dict() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        match_dict = ss.get_match_dict(match_id)
        assert isinstance(match_dict, dict)

    # ==============================================================================================
    def test_scrape_player_league_stats(self):
        """ Test the outputs of the scrape_player_league_stats() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        stats = ss.scrape_player_league_stats(year, league)
        assert isinstance(stats, pd.DataFrame)
        assert ((stats.shape[0] > 0) and (stats.shape[1] > 0)) or (stats.shape == (0,0))

    # ==============================================================================================
    def test_scrape_match_momentum(self):
        """ Test the outputs of the scrape_match_momentum() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        momentum = ss.scrape_match_momentum(match_id)
        assert isinstance(momentum, pd.DataFrame)
        assert ((momentum.shape[0] > 0) and (momentum.shape[1] > 0)) or (momentum.shape == (0,0))

    # ==============================================================================================
    def test_scrape_team_match_stats(self):
        """ Test the outputs of the scrape_team_match_stats() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        team_stats = ss.scrape_team_match_stats(match_id)
        assert isinstance(team_stats, pd.DataFrame)
        assert ((team_stats.shape[0] > 0) and (team_stats.shape[1] > 0))\
            or (team_stats.shape == (0,0))

    # ==============================================================================================
    def test_scrape_player_match_stats(self):
        """ Test the outputs of the scrape_player_match_stats() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        player_stats = ss.scrape_player_match_stats(match_id)
        assert isinstance(player_stats, pd.DataFrame)
        assert ((player_stats.shape[0] > 0) and (player_stats.shape[1] > 0))\
            or (player_stats.shape == (0,0))

    # ==============================================================================================
    def test_scrape_player_average_positions(self):
        """ Test the outputs of the scrape_player_average_positions() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        avg_pos = ss.scrape_player_average_positions(match_id)
        assert isinstance(avg_pos, pd.DataFrame)
        assert ((avg_pos.shape[0] > 0) and (avg_pos.shape[1] > 0)) or (avg_pos.shape == (0,0))

    # ==============================================================================================
    def test_scrape_heatmaps(self):
        """ Test the outputs of the scrape_player_average_positions() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        heatmaps = ss.scrape_heatmaps(match_id)
        # Output is dict
        assert isinstance(heatmaps, dict)
        # Values are dict
        assert np.all([isinstance(x, dict) for x in heatmaps.values()])
        # Player ID is in all player dicts
        assert np.all(['id' in x.keys() for x in heatmaps.values()])
        # Player ID is an int
        assert np.all([isinstance(x['id'], int) for x in heatmaps.values()])
        # Heatmap coords are in all player dicts
        assert np.all(['heatmap' in x.keys() for x in heatmaps.values()])
        # Heatmap coords are a list
        assert np.all([isinstance(x['heatmap'], list) for x in heatmaps.values()])

    # ==============================================================================================
    def test_scrape_match_shots(self):
        """ Test the outputs of the scrape_match_shots() function
        """
        ss = Sofascore()
        league = random.sample(list(comps.keys()), 1)[0]
        year = random.sample(list(ss.get_valid_seasons(league).keys()), 1)[0]

        match_dicts = ss.get_match_dicts(year, league)
        match_id = random.sample(match_dicts, 1)[0]['id']
        shots = ss.scrape_match_shots(match_id)
        assert isinstance(shots, pd.DataFrame)
        assert shots.shape[0] >= 0
        assert shots.shape[1] >= 0

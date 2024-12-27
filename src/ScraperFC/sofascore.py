import pandas as pd
from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from .utils import botasaurus_get
import numpy as np
from typing import Union, Sequence
import warnings

""" These are the status codes for Sofascore events. Found in event['status'] key.
{100: {'code': 100, 'description': 'Ended', 'type': 'finished'},
 120: {'code': 120, 'description': 'AP', 'type': 'finished'},
 110: {'code': 110, 'description': 'AET', 'type': 'finished'},
 70: {'code': 70, 'description': 'Canceled', 'type': 'canceled'},
 60: {'code': 60, 'description': 'Postponed', 'type': 'postponed'},
 93: {'code': 93, 'description': 'Removed', 'type': 'finished'},
 90: {'code': 90, 'description': 'Abandoned', 'type': 'canceled'},
 7: {'code': 7, 'description': '2nd half', 'type': 'inprogress'},
 6: {'code': 6, 'description': '1st half', 'type': 'inprogress'},
 0: {'code': 0, 'description': 'Not started', 'type': 'notstarted'}}
"""

API_PREFIX = 'https://api.sofascore.com/api/v1'

comps = {
    # European continental club comps
    'Champions League': 7, 'Europa League': 679, 'Europa Conference League': 17015,
    # European domestic leagues
    'EPL': 17, 'La Liga': 8, 'Bundesliga': 35, 'Serie A': 23, 'Ligue 1': 34, 'Turkish Super Lig': 52,
    # South America
    'Argentina Liga Profesional': 155, 'Argentina Copa de la Liga Profesional': 13475,
    'Liga 1 Peru': 406, "Copa Libertadores": 384,
    # USA
    'MLS': 242, 'USL Championship': 13363, 'USL1': 13362, 'USL2': 13546,
    # Middle East
    "Saudi Pro League": 955,
    # Men's international comps
    'World Cup': 16, 'Euros': 1, 'Gold Cup': 140,
    # Women's international comps
    "Women's World Cup": 290
}


class Sofascore:
    
    # ==============================================================================================
    def __init__(self) -> None:
        self.league_stats_fields = [
            'goals', 'yellowCards', 'redCards', 'groundDuelsWon', 'groundDuelsWonPercentage',
            'aerialDuelsWon', 'aerialDuelsWonPercentage', 'successfulDribbles',
            'successfulDribblesPercentage', 'tackles', 'assists', 'accuratePassesPercentage',
            'totalDuelsWon', 'totalDuelsWonPercentage', 'minutesPlayed', 'wasFouled', 'fouls',
            'dispossessed', 'possesionLost', 'appearances', 'started', 'saves', 'cleanSheets',
            'savedShotsFromInsideTheBox', 'savedShotsFromOutsideTheBox',
            'goalsConcededInsideTheBox', 'goalsConcededOutsideTheBox', 'highClaims',
            'successfulRunsOut', 'punches', 'runsOut', 'accurateFinalThirdPasses',
            'bigChancesCreated', 'accuratePasses', 'keyPasses', 'accurateCrosses',
            'accurateCrossesPercentage', 'accurateLongBalls', 'accurateLongBallsPercentage',
            'interceptions', 'clearances', 'dribbledPast', 'bigChancesMissed', 'totalShots',
            'shotsOnTarget', 'blockedShots', 'goalConversionPercentage', 'hitWoodwork', 'offsides',
            'expectedGoals', 'errorLeadToGoal', 'errorLeadToShot', 'passToAssist'
        ]
        self.concatenated_fields = '%2C'.join(self.league_stats_fields)

    # ==============================================================================================
    def _check_and_convert_to_match_id(self, match: Union[str, int]) -> int:
        """ Helper function that will take a Sofascore match URL or match ID and return a match ID

        Parameters
        ----------
        match : str or int
            Strings will be interprated as URLs and ints will be interpreted as match IDs.

        Returns
        -------
        match_id : int
        """
        if not isinstance(match, int) and not isinstance(match, str):
            raise TypeError('`match` must a string or int')
        match_id = match if isinstance(match, int) else self.get_match_id_from_url(match)
        return match_id

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """ Returns the valid seasons and their IDs for the given league

        Parameters
        ----------
        league : str
            League to get valid seasons for. See comps ScraperFC.Sofascore for valid leagues.
        
        Returns
        -------
        seasons : dict
            Available seasons for the league. {season string: season ID, ...}
        """
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Sofascore', list(comps.keys()))
            
        response = botasaurus_get(f'{API_PREFIX}/unique-tournament/{comps[league]}/seasons/')
        seasons = dict([(x['year'], x['id']) for x in response.json()['seasons']])
        return seasons

    # ==============================================================================================
    def get_match_dicts(self, year: str, league:str) -> Sequence[dict]:
        """ Returns the matches from the Sofascore API for a given league season.

        Parameters
        ----------
        year : str
            See the :ref:`sofascore_year` `year` parameter docs for details.
        league : str
            League to get valid seasons for. See comps ScraperFC.Sofascore for valid leagues.
        
        Returns
        -------
        matches : list of dict
            Each element being a single game of the competition
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        matches = list()
        i = 0
        while 1:
            response = botasaurus_get(
                f'{API_PREFIX}/unique-tournament/{comps[league]}/season/{valid_seasons[year]}/' +
                f'events/last/{i}'
            )
            if response.status_code != 200:
                break
            matches += response.json()['events']
            i += 1

        return matches

    # ==============================================================================================
    def get_match_id_from_url(self, match_url: str) -> int:
        """ Get match id from a Sofascore match URL.
        
        This can also be found in the 'id' key of the dict returned from get_match_dict().

        Parameters
        ----------
        match_url : str
            Full link to a SofaScore match

        Returns
        -------
        : int
            Match id for a SofaScore match
        """
        if not isinstance(match_url, str):
            raise TypeError('`match_url` must be a string.')
        match_id = int(match_url.split('#id:')[-1])
        return match_id

    # ==============================================================================================
    def get_match_url_from_id(self, match_id: Union[str, int]) -> str:
        """ Get the Sofascore match URL for a given match ID

        Parameters
        ----------
        match_id : str or int
            Sofascore match ID

        Returns
        -------
        : str
            URL to the Sofascore match
        """
        match_dict = self.get_match_dict(match_id)
        return f"https://www.sofascore.com/{match_dict['homeTeam']['slug']}-" +\
            f"{match_dict['awayTeam']['slug']}/{match_dict['customId']}#id:{match_dict['id']}"

    # ==============================================================================================
    def get_match_dict(self, match: Union[str, int]) -> dict:
        """ Get match data dict for a single match

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        -------
        : dict
            Generic data about a match
        """
        match_id = self._check_and_convert_to_match_id(match)
        response = botasaurus_get(f'{API_PREFIX}/event/{match_id}')
        data = response.json()['event']
        return data

    # ==============================================================================================
    def get_team_names(self, match: Union[str, int]) -> tuple[str, str]:
        """ Get the team names for the home and away teams

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        -------
        : tuple of str
            Name of home and away team.
        """
        data = self.get_match_dict(match)
        home_team = data['homeTeam']['name']
        away_team = data['awayTeam']['name']
        return home_team, away_team
    
    # ==============================================================================================
    def get_positions(self, selected_positions: Sequence[str]) -> str:
        """ Returns a string for the parameter filters of the scrape_league_stats() request.

        Parameters
        ----------
        selected_positions : list of str
            List of the positions available to filter on the SofaScore UI

        Returns
        -------
        : str
            Joined abbreviations for the chosen positions
        """
        positions = {'Goalkeepers': 'G', 'Defenders': 'D', 'Midfielders': 'M', 'Forwards': 'F'}
        if not isinstance(selected_positions, list):
            raise TypeError('`selected_positions` must be a list.')
        if not np.all([isinstance(x, str) for x in selected_positions]):
            raise TypeError('All items in `selected_positions` must be strings.')
        if not np.isin(selected_positions, list(positions.keys())).all():
            raise ValueError(f'All items in `selected_positions` must be in {positions.keys()}')
            
        abbreviations = [positions[position] for position in selected_positions]
        return '~'.join(abbreviations)
    
    # ==============================================================================================
    def get_player_ids(self, match: Union[str, int]) -> dict:
        """ Get the player IDs for a match
        
        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        -------
        : dict
            Name and ID of every player in the match, {name: id, ...}
        """
        match_id = self._check_and_convert_to_match_id(match)
        url = f"{API_PREFIX}/event/{match_id}/lineups"
        response = botasaurus_get(url)
        teams = ['home', 'away']
        if response.status_code == 200:
            player_ids = dict()
            for team in teams:
                data = response.json()[team]['players']
                for item in data:
                    player_data = item['player']
                    player_ids[player_data['name']] = player_data['id']
        else:
            warnings.warn(f"\nReturned {response.status_code} from {url}. Returning empty dict.")
            player_ids = dict()

        return player_ids
    
    # ==============================================================================================
    def scrape_player_league_stats(
            self, year: str, league: str, accumulation: str='total',
            selected_positions: Sequence[str]=[
                'Goalkeepers', 'Defenders', 'Midfielders', 'Forwards'
            ]
        ) -> pd.DataFrame:
        """ Get every player statistic that can be asked in league pages on Sofascore.

        Parameters
        ----------
        year : str
            See the :ref:`sofascore_year` `year` parameter docs for details.
        league : str
            League to get valid seasons for. See comps ScraperFC.Sofascore for valid leagues.
        accumulation : str, optional
            Value of the filter accumulation. Can be "per90", "perMatch", or "total". Defaults to
            "total".
        selected_positions : list of str, optional
            Value of the filter positions. Defaults to ["Goalkeepers", "Defenders", "Midfielders",
            "Forwards"].

        Returns
        -------
        : DataFrame
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))
        if not isinstance(accumulation, str):
            raise TypeError('`accumulation` must be a string.')
        valid_accumulations = ['total', 'per90', 'perMatch']
        if accumulation not in valid_accumulations:
            raise ValueError(f'`accumulation` must be one of {valid_accumulations}')
        
        positions = self.get_positions(selected_positions)
        season_id = valid_seasons[year]
        league_id = comps[league]
        
        # Get all player stats from Sofascore API
        offset = 0
        results = list()
        while 1:
            request_url = 'https://api.sofascore.com/api/v1' +\
                f'/unique-tournament/{league_id}/season/{season_id}/statistics' +\
                f'?limit=100&offset={offset}' +\
                f'&accumulation={accumulation}' +\
                f'&fields={self.concatenated_fields}' +\
                f'&filters=position.in.{positions}'
            response = botasaurus_get(request_url)
            results += response.json()['results']
            if (response.json()['page'] == response.json()['pages']) or\
                    (response.json()['pages'] == 0):
                break
            offset += 100

        # Convert the player dicts to a dataframe. Dataframe will be empty if there aren't any
        # player stats
        if len(results) == 0:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame.from_dict(results)  # type: ignore
            df['player id'] = df['player'].apply(pd.Series)['id']
            df['player'] = df['player'].apply(pd.Series)['name']
            df['team id'] = df['team'].apply(pd.Series)['id']
            df['team'] = df['team'].apply(pd.Series)['name']
        
        return df

    # ==============================================================================================
    def scrape_match_momentum(self, match: Union[str, int]) -> pd.DataFrame:
        """Get the match momentum values

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        --------
        : DataFrame
            Dataframe of match momentum values. Will be empty if the match does not have
            match momentum data.
        """
        match_id = self._check_and_convert_to_match_id(match)
        url = f'{API_PREFIX}/event/{match_id}/graph'
        response = botasaurus_get(url)
        if response.status_code == 200:
            match_momentum_df = pd.DataFrame(response.json()['graphPoints'])
        else:
            warnings.warn(f"\nReturned {response.status_code} from {url}. Returning empty dataframe.")
            match_momentum_df = pd.DataFrame()

        return match_momentum_df

    # ==============================================================================================
    def scrape_team_match_stats(self, match: Union[str, int]) -> pd.DataFrame:
        """ Scrape team stats for a match

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        -------
        : DataFrame
        """
        match_id = self._check_and_convert_to_match_id(match)
        url = f'{API_PREFIX}/event/{match_id}/statistics'
        response = botasaurus_get(url)
        if response.status_code == 200:
            df = pd.DataFrame()
            for period in response.json()['statistics']:
                period_name = period['period']
                for group in period['groups']:
                    group_name = group['groupName']
                    temp = pd.DataFrame.from_dict(group['statisticsItems'])
                    temp['period'] = [period_name,] * temp.shape[0]
                    temp['group'] = [group_name,] * temp.shape[0]
                    df = pd.concat([df, temp], ignore_index=True)
        else:
            warnings.warn(f"\nReturned {response.status_code} from {url}. Returning empty dataframe.")
            df = pd.DataFrame()
        
        return df

    # ==============================================================================================
    def scrape_player_match_stats(self, match: Union[str, int]) -> pd.DataFrame:
        """ Scrape player stats for a match

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        -------
        : DataFrame
        """
        match_id = self._check_and_convert_to_match_id(match)
        match_dict = self.get_match_dict(match_id)  # used to get home and away team names and IDs
        url = f'{API_PREFIX}/event/{match_id}/lineups'
        response = botasaurus_get(url)
        
        if response.status_code == 200:
            home_players = response.json()['home']['players']
            away_players = response.json()['away']['players']
            for p in home_players:
                p["teamId"] = match_dict["homeTeam"]["id"]
                p["teamName"] = match_dict["homeTeam"]["name"]
            for p in away_players:
                p["teamId"] = match_dict["awayTeam"]["id"]
                p["teamName"] = match_dict["awayTeam"]["name"]
                players = home_players + away_players
                
            temp = pd.DataFrame(players)
            columns = list()
            for c in temp.columns:
                if isinstance(temp.loc[0, c], dict):
                    # Break dicts into series
                    columns.append(temp[c].apply(pd.Series, dtype=object))
                else:
                    # Else they're already series
                    columns.append(temp[c])  # type: ignore
            df = pd.concat(columns, axis=1)
        else:
            warnings.warn(f"\nReturned {response.status_code} from {url}. Returning empty dataframe.")
            df = pd.DataFrame()
        
        return df

    # ==============================================================================================
    def scrape_player_average_positions(self, match: Union[str, int]) -> pd.DataFrame:
        """ Return player averages positions for each team

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID

        Returns
        -------
        : DataFrame
            Each row is a player and columns averageX and averageY denote their average position on
            the match.
        """
        match_id = self._check_and_convert_to_match_id(match)
        home_name, away_name = self.get_team_names(match)
        url = f'{API_PREFIX}/event/{match_id}/average-positions'
        response = botasaurus_get(url)
        if response.status_code == 200:
            df = pd.DataFrame()
            for key, name in [('home', home_name), ('away', away_name)]:
                temp = pd.DataFrame(response.json()[key])
                temp['team'] = [name,] * temp.shape[0]
                temp = pd.concat(
                    [temp['player'].apply(pd.Series), temp.drop(columns=['player'])],
                    axis=1
                )
                df = pd.concat([df, temp], axis=0, ignore_index=True)
        else:
            warnings.warn(f"\nReturned {response.status_code} from {url}. Returning empty dataframe.")
            df = pd.DataFrame()
        return df
    
    # ==============================================================================================
    def scrape_heatmaps(self, match: Union[str, int]) -> dict:
        """ Get the x-y coordinates to create a player heatmap for all players in the match.

        Players who didn't play will have an empty list of coordinates.

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID
        
        Returns
        -------
        : dict
            Dict of players, their IDs and their heatmap coordinates, {player name: {'id':
            player_id, 'heatmap': heatmap}, ...}
        """
        match_id = self._check_and_convert_to_match_id(match)
        players = self.get_player_ids(match)
        for player in players:
            player_id = players[player]
            url = f'{API_PREFIX}/event/{match_id}/player/{player_id}/heatmap'
            response = botasaurus_get(url)
            if response.status_code == 200:
                heatmap = [(z['x'], z['y']) for z in response.json()['heatmap']]
            else:
                # Players that didn't play have empty heatmaps. Don't print warning because there
                # would be a lot of them.
                heatmap = list()
            players[player] = {'id': player_id, 'heatmap': heatmap}
        return players
    
    # ==============================================================================================
    def scrape_match_shots(self, match: Union[str, int]) -> pd.DataFrame:
        """ Scrape shots for a match

        Parameters
        ----------
        match : str or int
            Sofascore match URL or match ID
        
        Returns
        -------
        : DataFrame
        """
        match_id = self._check_and_convert_to_match_id(match)
        url = f"{API_PREFIX}/event/{match_id}/shotmap"
        response = botasaurus_get(url)
        if response.status_code == 200:
            df = pd.DataFrame.from_dict(response.json()["shotmap"])
        else:
            warnings.warn(
                f"Returned {response.status_code} from {url}. Returning empty dataframe."
            )
            df = pd.DataFrame()
        return df

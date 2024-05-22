# import requests
import json
import pandas as pd
from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from botasaurus import request, AntiDetectRequests
import numpy as np

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
    'EPL': 17, 'La Liga': 8, 'Bundesliga': 35, 'Serie A': 23, 'Ligue 1': 34,
    # South America
    'Argentina Liga Profesional': 155, 'Argentina Copa de la Liga Profesional': 13475,
    'Liga 1 Peru': 406,
    # USA
    'MLS': 242, 'USL Championship': 13363, 'USL1': 13362, 'USL2': 13546,
    # Men's international comps
    'World Cup': 16, 'Euros': 1, 'Gold Cup': 140,
    # Women's international comps
    "Women's World Cup": 290
}

@request(use_stealth=True, output=None, create_error_logs=False)
def _botasaurus_get(request: AntiDetectRequests, url):
    """ Sofascore introduced some anti-scraping measures. Using Botasaurus gets aroudn them.
    """
    if type(url) is not str:
        raise TypeError('`url` must be a string.')
    response = request.get(url)
    return response

class Sofascore:
    
    # ==============================================================================================
    def __init__(self):
        # self.requests_headers = {
        #     'authority': 'api.sofascore.com',
        #     'accept': '*/*',
        #     'accept-language': 'en-US,en;q=0.9',
        #     'cache-control': 'max-age=0',
        #     'dnt': '1',
        #     'if-none-match': 'W/"4bebed6144"',
        #     'origin': 'https://www.sofascore.com',
        #     'referer': 'https://www.sofascore.com/',
        #     'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114"',
        #     'sec-ch-ua-mobile': '?0',
        #     'sec-ch-ua-platform': '"macOS"',
        #     'sec-fetch-dest': 'empty',
        #     'sec-fetch-mode': 'cors',
        #     'sec-fetch-site': 'same-site',
        #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '+ \
        #         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 '+ \
        #         'Safari/537.36',
        #     }
        
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
    def get_valid_seasons(self, league):
        """ Returns the valid seasons and their IDs for the given league

        Args:
            league (str): League to get valid seasons for. See comps ScraperFC.Sofascore for valid 
                leagues.
        
        Returns:
            seasons (dict): Dict of available seasons for the league. 
                Key : season string
                Value: season ID
        """
        if type(league) is not str:
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Sofascore')
            
        response = _botasaurus_get(f'{API_PREFIX}/unique-tournament/{comps[league]}/seasons/')
        seasons = dict([(x['year'], x['id']) for x in response.json()['seasons']])
        return seasons

    # ==============================================================================================
    def get_match_dicts(self, year, league):
        """ Returns the matches from the Sofascore API for a given league season.

        Args:
            year (str): Year to scrape. Enter the year as it appears in the dropdown on the
                competition's homepage on Sofascore.
            league (str): League to get valid seasons for. See comps ScraperFC.Sofascore for valid 
                leagues.
        
        Returns:
            matches (list[dict]): list of dicts, each element being a single game of the competition
        """
        valid_seasons = self.get_valid_seasons(league)
        if type(year) is not str:
            raise TypeError('`year` must be a string.')
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league)

        matches = list()
        i = 0
        while 1:
            
            response = _botasaurus_get(f'{API_PREFIX}/unique-tournament/{comps[league]}/season/{valid_seasons[year]}/events/last/{i}')
            if response.status_code != 200:
                break
            matches += response.json()['events']
            i += 1

        return matches

    # ==============================================================================================
    def get_match_id_from_url(self, match_url):
        """ Get match id from a Sofascore match URL. 
        
        This can also be found in the 'id' key of the dict returned from get_match_dict().

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            string: Match id for a SofaScore match. Used in Urls
        """
        if type(match_url) is not str:
            raise TypeError('`match_url` must be a string.')
        
        match_id = int(match_url.split('#id:')[-1])
        return match_id

    # ==============================================================================================
    def get_match_dict(self, match_id):
        """ Get match data dict from a Sofascore match ID.

        Args:
            match_id (int): Sofascore match ID

        Returns:
            dict: Generic data about a match
        """
        if type(match_id) is not int:
            raise TypeError('`match_id` must be an int.')

        response = _botasaurus_get(f'{API_PREFIX}/event/{match_id}')
        data = response.json()['event']

        return data
    
    def get_match_dict_from_url(self, match_url):  # ===============================================
        """ Get match data dict from a Sofascore URL.

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            dict: Generic data about a match
        """
        match_id = self.get_match_id_from_url(match_url)
        return self.get_match_dict(match_id)

    # # ==============================================================================================
    # def get_team_names(self, match_url):
    #     """ Get the team names for the home and away teams

    #     Args:
    #         match_url (string): Full link to a Sofascore match

    #     Returns:
    #         strings: Name of home and away team.
    #     """
    #     data = self.get_match_data(match_url)

    #     home_team = data['homeTeam']['name']
    #     away_team = data['awayTeam']['name']

    #     return home_team, away_team

    
    # ==============================================================================================
    def get_positions(self, selected_positions):
        """ Returns a string for the parameter filters of the scrape_league_stats() request.

        Args:
            selected_positions (list): List of the positions available to filter on the SofaScore UI

        Returns:
            str: joined abbreviations for the chosen positions
        """
        positions = {'Goalkeepers': 'G', 'Defenders': 'D', 'Midfielders': 'M', 'Forwards': 'F'}
        if type(selected_positions) is not list:
            raise TypeError('`selected_positions` must be a list.')
        if not np.all([type(x) is str for x in selected_positions]):
            raise TypeError('All items in `selected_positions` must be strings.')
        if not np.isin(selected_positions, list(positions.keys())).all():
            raise ValueError(f'All items in `selected_positions` must be in {positions.keys()}')
            
        abbreviations = [positions[position] for position in selected_positions]
        return '~'.join(abbreviations)
    
    # ==============================================================================================
    def get_player_ids(self, match_id):
        """ Get the player IDs for a match from the match ID
        
        Args:
            match_id (int): Sofascore match ID

        Returns:
            dict: Name and ids of every player in the match
                Key: Name
                Value: Id
        """
        if type(match_id) is not int:
            raise TypeError('`match_id` must be an int.')
        response = _botasaurus_get(f'{API_PREFIX}/event/{match_id}/lineups')

        teams = ['home', 'away']
        player_ids = {}
        for team in teams:
            data = response.json()[team]['players']

            for item in data:
                player_data = item['player']
                player_ids[player_data['name']] = player_data['id']

        return player_ids
        
    def get_player_ids_from_url(self, match_url):  # ===============================================
        """Get the player ids for a Sofascore match from the match URL

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            dict: Name and ids of every player in the match
                Key: Name
                Value: Id
        """
        match_id = self.get_match_id_from_url(match_url)
        return self.get_player_ids(match_id)
    
    # ==============================================================================================
    def scrape_player_stats(
        self, year, league, accumulation='total', 
        selected_positions=['Goalkeepers', 'Defenders', 'Midfielders', 'Forwards']
    ):
        """ Get every player statistic that can be asked in league pages on 
        SofaScore.

        Args:
            tournament (string): Name of the competition
            season (string): Season selected
            accumulation (str, optional): Value of the filter accumulation. Can be "per90", 
                "perMatch", or "total". Defaults to 'total'.
            selected_positions (list, optional): Value of the filter positions. Defaults to [
                'Goalkeepers', 'Defenders', 'Midfielders','Forwards'].

        Returns:
            DataFrame: DataFrame with each row corresponding to a player and 
                the columns are the fields defined on self.concatenated_fields
        """
        if type(accumulation) is not str:
            raise TypeError('`accumulation` must be a string.')
        valid_accumulations = ['total', 'per90', 'perMatch']
        if accumulation not in valid_accumulations:
            raise ValueError(f'`accumulation` must be one of {valid_accumulations}')
        
        positions = self.get_positions(selected_positions)
        season_id = self.get_valid_seasons(league)[year]
        league_id = comps[league]
        
        offset = 0
        df = pd.DataFrame()
        while 1:
            request_url = f'https://api.sofascore.com/api/v1' +\
                f'/unique-tournament/{league_id}/season/{season_id}/statistics'+\
                f'?limit=100&offset={offset}'+\
                f'&accumulation={accumulation}' +\
                f'&fields={self.concatenated_fields}'+\
                f'&filters=position.in.{positions}'
            response = _botasaurus_get(request_url)
            new_df = pd.DataFrame(response.json()['results'])
            new_df['player'] = new_df.player.apply(pd.Series)['name']
            new_df['team'] = new_df.team.apply(pd.Series)['name']
            df = pd.concat([df, new_df])
            
            if response.json().get('page') == response.json().get('pages'):
                break
            offset += 100
        
        return df

    # ==============================================================================================
    def scrape_match_momentum_from_url(self, match_url):
        """Get the match momentum values

        Args:
            match_url (str): Full link to a SofaScore match

        Returns:
            fig, ax: Plot of match momentum and fig/axes for further customization
        """
        match_id = self.get_match_id_from_url(match_url)
        response = _botasaurus_get(f'{API_PREFIX}/event/{match_id}/graph')
        match_momentum_df = pd.DataFrame(response.json()['graphPoints'])

        return match_momentum_df

    # ############################################################################
    # def get_general_match_stats(self, match_url):
    #     """Get general match statistics (possession, passes, duels) by teams.

    #     Args:
    #         match_url (str): Full link to a SofaScore match

    #     Returns:
    #         DataFrame: Each row is a general statistic and the columns show the 
    #             values for home and away Teams.
    #     """
    #     match_id = self.get_match_id(match_url)

    #     response = requests.get(
    #         f'https://api.sofascore.com/api/v1/event/{match_id}/statistics', 
    #         headers=self.requests_headers
    #     )

    #     df = pd.DataFrame()
    #     for i in range(len(response.json()['statistics'][0]['groups'])):
    #         df_valores = pd.DataFrame(response.json()['statistics'][0]['groups'][i]['statisticsItems'])
    #         df = pd.concat([df,df_valores])
    #     df = df[['name', 'home', 'homeValue', 'homeTotal','away', 'awayValue', 'awayTotal']]
    #     return df
    
    # ############################################################################
    # def get_players_match_stats(self, match_url):
    #     """Returns match data for each player.

    #     Args:
    #         match_url (str): Full link to a SofaScore match

    #     Returns:
    #         DataFrames: A DataFrame for home and away teams with each row being 
    #             a player and in each columns a different statistic or data of 
    #             the player
    #     """

    #     match_id = self.get_match_id(match_url)
    #     home_name, away_name = self.get_team_names(match_url)
        
    #     response = requests.get(
    #         f'https://api.sofascore.com/api/v1/event/{match_id}/lineups', 
    #         headers=self.requests_headers
    #     )
        
    #     names = {'home': home_name, 'away': away_name}
    #     dataframes = {}
    #     for team in names.keys():
    #         data = pd.DataFrame(response.json()[team]['players'])
    #         columns_list = [
    #             data['player'].apply(pd.Series), data['shirtNumber'], 
    #             data['jerseyNumber'], data['position'], data['substitute'], 
    #             data['statistics'].apply(pd.Series, dtype=object), 
    #             data['captain']
    #         ]
    #         df = pd.concat(columns_list, axis=1)
    #         df['team'] = names[team]
    #         dataframes[team] = df
        
    #     return dataframes['home'], dataframes['away']
    
    # ############################################################################
    # def get_players_average_positions(self, match_url):
    #     """Return player averages positions for each team

    #     Args:
    #         match_url (str): Full link to a SofaScore match

    #     Returns:
    #         DataFrame: Each row is a player and columns averageX and averageY 
    #             denote their average position on the match.
    #     """
    #     match_id = self.get_match_id(match_url)
    #     home_name, away_name = self.get_team_names(match_url)

    #     response = requests.get(
    #         f'https://api.sofascore.com/api/v1/event/{match_id}/average-positions', 
    #         headers=self.requests_headers
    #     )

    #     names = {'home': home_name, 'away': away_name}
    #     dataframes = {}
    #     for team in names.keys():
    #         data = pd.DataFrame(response.json()[team])
    #         df = pd.concat(
    #             [data['player'].apply(pd.Series), data.drop(columns=['player'])],
    #             axis=1
    #         )
    #         df['team'] = names[team]
    #         dataframes[team] = df
            
    #     return dataframes['home'], dataframes['away']
    
    # ############################################################################
    # def get_player_heatmap(self, match_url, player):
    #     """ Get the x-y coordinates to create a player heatmap. Use Seaborn's
    #     `kdeplot()` to create the heatmap image.

    #     Args:
    #         match_url (str): Full link to a SofaScore match
    #         player (str): Name of the player (must be the SofaScore one). Use
    #             Sofascore.get_player_ids()

    #     Returns:
    #         DataFrame: Pandas dataframe with x-y coordinates for the player
    #     """
    #     match_id = self.get_match_id(match_url)

    #     player_ids = self.get_player_ids(match_url)
    #     player_id = player_ids[player]

    #     response = requests.get(
    #         f'https://api.sofascore.com/api/v1/event/{match_id}/player/{player_id}/heatmap', 
    #         headers=self.requests_headers
    #     )
    #     heatmap = pd.DataFrame(response.json()['heatmap'])
        
    #     return heatmap

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch


class SofaScore:

    def get_requests_headers(self):
        """Returns headers for all the requests to SofaScore API

        Returns:
            dict: headers for request
        """
        headers = {
            'authority': 'api.sofascore.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'dnt': '1',
            'if-none-match': 'W/"4bebed6144"',
            'origin': 'https://www.sofascore.com',
            'referer': 'https://www.sofascore.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            }
        return headers

    def get_league_stats_fields(self):
        """Returns a dict with all the fields selectable for player league statistics within SofaScore. The values are not the name that appears
        on the SofaScore UI, but the ones that make the query param "fields" of the request.

        Returns:
            list: statistics for league scraping
        """
        fields = [
            'goals',
            'yellowCards',
            'redCards',
            'groundDuelsWon',
            'groundDuelsWonPercentage',
            'aerialDuelsWon',
            'aerialDuelsWonPercentage',
            'successfulDribbles',
            'successfulDribblesPercentage'
            'tackles',
            'assists',
            'accuratePassesPercentage',
            'totalDuelsWon',
            'totalDuelsWonPercentage',
            'minutesPlayed',
            'wasFouled',
            'fouls',
            'dispossessed',
            'possesionLost',
            'appearances',
            'started',
            'saves',
            'cleanSheets',
            'savedShotsFromInsideTheBox',
            'savedShotsFromOutsideTheBox',
            'goalsConcededInsideTheBox',
            'goalsConcededOutsideTheBox',
            'highClaims',
            'successfulRunsOut',
            'punches',
            'runsOut',
            'accurateFinalThirdPasses',
            'bigChancesCreated',
            'accuratePasses',
            'keyPasses',
            'accurateCrosses',
            'accurateCrossesPercentage',
            'accurateLongBalls',
            'accurateLongBallsPercentage',
            'interceptions',
            'clearances',
            'dribbledPast',
            'bigChancesMissed',
            'totalShots',
            'shotsOnTarget',
            'blockedShots',
            'goalConversionPercentage',
            'hitWoodwork',
            'offsides',
            'expectedGoals',
            'errorLeadToGoal',
            'errorLeadToShot',
            'passToAssist'
        ]
        return fields
    
    def get_tournaments_ids(self):
        """Returns the SofaScore league id (that appears on the URL).
        Example: https://www.sofascore.com/tournament/football/argentina/copa-de-la-liga-profesional/13475#47644 --> 13475 is the league id

        Returns:
            dict: 
                Key: League
                Value: League id
        """
        tournaments_ids = {
            'La Liga': 8,
            'Premier League': 17,
            'Copa de la Liga Profesional': 13475
        }
        return tournaments_ids

    def get_seasons(self, season, tournament):
        """Returns the SofaScore seasons id (that appears on the URL)
        Example: https://www.sofascore.com/tournament/football/argentina/copa-de-la-liga-profesional/13475#47644 --> 47644 is the season id
        Seasons may vary if the leagues start on January or June/July.

        Returns:
            dict: 
                Key: Season
                Value: Season id
        """

        season_ids = {
            '23/24': 52186,
            '22/23': 41886,
            '2023': 47644,
            '2021/22': 37036,
            '2022': 40377,
            '2020/21': 29415,
            '2021': 35486,
            '2019/20': 23776,
            '2020': 34618,
            '2018/19': 17359,
            '2019': 23108
        }
        
        return season_ids
    
    def get_positions(self, selected_positions):
        """Returns a string for the parameter filters of the scrape_league_stats() request.

        Args:
            selected_positions (list): List of the positions available to filter on the SofaScore UI

        Returns:
            dict: Goalies, Defenders, Midfielders and Forwards and their translation for the parameter of the request
        """
        positions = {
            'Goalkeepers': 'G',
            'Defenders': 'D',
            'Midfielders': 'M',
            'Forwards': 'F'
        }
        abbreviations = [positions[position] for position in selected_positions]
        return '~'.join(abbreviations)

    def concatenate_fields(self, fields):
        """Returns a string for the parameter fields of the scrape_league_stats() request.

        Args:
            fields (list): the return of the get_league_stats_fields()

        Returns:
            string: the full string to put in the parameters "fields" with every field separated by a %2C as the request does in the SofaScore page.
        """
        fields_request = "%2C".join(f"{fields[i]}" for i in range(len(fields)))
        return fields_request
    
    def get_player_ids(self, match_url):
        """Get the player ids for any match

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            dict: Name and ids of every player in the match
                Key: Name
                Value: Id
        """
        match_id = self.get_match_id(match_url)
        headers = self.get_requests_headers()

        response = requests.get(f'https://api.sofascore.com/api/v1/event/{match_id}/lineups', headers=headers)

        teams = ['home', 'away']
        player_ids = {}
        for team in teams:
            data = response.json()[team]['players']

            for item in data:
                player_data = item['player']
                player_ids[player_data['name']] = player_data['id']

        return player_ids
    
    def get_match_data(self, match_url):
        """Get match general data

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            dict/json: Generic data about a match in particular
        """

        match_id = self.get_match_id(match_url)
        headers = self.get_requests_headers()

        response = requests.get(f'https://api.sofascore.com/api/v1/event/{match_id}', headers=headers)
        data = response.json()['event']
        return data
    
    def get_team_names(self, match_url):
        """Get the team names for the home and away teams

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            strings: Name of home and away team.
        """

        data = self.get_match_data(match_url)

        home_team = data['homeTeam']['name']
        away_team = data['awayTeam']['name']

        return home_team, away_team

    def match_momentum_plot(self, match_momentum_df, match_id, colors = ['red', 'green']):
        """Plot Match Momentum replicating the one on SofaScore UI

        Args:
            match_momentum_df (DataFrame): DataFrame generated in match_momentum functions. Contains two columns: Minute and value (if > 0, momentum was with home side and viceversa)
            match_id (string): Match Id for a SofaScore match
            colors (list, optional): Colors of the bars in the graph. Defaults to ['red', 'green'].

        Returns:
            fig, ax: A png and the fig and axes for further customization
        """

        plot_colors = [f'{colors[0]}' if value < 0 else f'{colors[1]}' for value in match_momentum_df.value]

        fig,ax = plt.subplots(figsize=(16,9))
        fig.set_facecolor('white')

        ax.bar(match_momentum_df.minute, match_momentum_df.value, color=plot_colors)
        ax.axvline(45.5, ls=':')
        ax.set_xlabel('Minutes')
        ax.set_xticks(range(0,91,10))
        ax.set_xlim(0,91)

        plt.gca()
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.set_yticks([])
        plt.savefig(f'{match_id}_match_momentum.png', bbox_inches='tight')
        
        return fig, ax
    
    def get_match_id(self, match_url):
        """Get match id for any match

        Args:
            match_url (string): Full link to a SofaScore match

        Returns:
            string: Match id for a SofaScore match. Used in Urls
        """
        match_id = match_url.split('#')[-1]
        return match_id

    def scrape_league_stats(self, tournament, season, accumulation='total', selected_positions=['Goalkeepers', 'Defenders', 'Midfielders', 'Forwards']):
        """Get every player statistic that can be asked in league pages on SofaScore.

        Args:
            tournament (string): Name of the competition
            season (string): Season selected
            accumulation (str, optional): Value of the filter accumulation. Can be "per90" and "perMatch". Defaults to 'total'.
            selected_positions (list, optional): Value of the filter positions. Defaults to ['Goalkeepers', 'Defenders', 'Midfielders', 'Forwards'].

        Returns:
            DataFrame: DataFrame with each row corresponding to a player and the columns are the fields defined on get_league_stats_fields()
        """
        df = pd.DataFrame()
        
        offset = 0

        headers = self.get_requests_headers()
        positions = self.get_positions(selected_positions)
        season_fields = self.get_league_stats_fields()
        fields = self.concatenate_fields(season_fields)
        positions = self.get_positions(selected_positions)
        season = self.get_seasons(season, tournament)
        tournaments_ids = self.get_tournaments_ids()

        for i in range(0,100):
            url = f'https://api.sofascore.com/api/v1/unique-tournament/{tournaments_ids[tournament]}/season/{season}/statistics?limit=100&order=-rating&offset={offset}&accumulation={accumulation}&fields={fields}&filters=position.in.{positions}'
            response = requests.get(url, headers=headers)
            new_df = pd.DataFrame(response.json()['results'])
            new_df['player'] = new_df.player.apply(pd.Series)['name']
            new_df['team'] = new_df.team.apply(pd.Series)['name']
            df = pd.concat([df, new_df])
            
            page = response.json().get('page')
            pages = response.json().get('pages')

            if page == pages:
                print('End of the pages')
                break
            offset += 100
        
        return df

    def match_momentum(self, match_url):
        """Get the match momentum plot

        Args:
            match_url (str): Full link to a SofaScore match

        Returns:
            fig, ax: Plot of match momentum and fig/axes for further customization
        """
        headers = self.get_requests_headers()
        match_id = self.get_match_id(match_url)
        graph_url = f'https://api.sofascore.com/api/v1/event/{match_id}/graph'
        response = requests.get(graph_url, headers=headers)
        match_momentum_df = pd.DataFrame(response.json()['graphPoints'])

        fig, ax = self.match_momentum_plot(match_momentum_df, match_id)

        return fig, ax

    def get_general_match_stats(self, match_url):
        """Get general match statistics (possession, passes, duels) by teams.

        Args:
            match_url (str): Full link to a SofaScore match

        Returns:
            DataFrame: Each row is a general statistic and the columns show the values for home and away Teams.
        """
        match_id = self.get_match_id(match_url)
        headers = self.get_requests_headers()

        response = requests.get(f'https://api.sofascore.com/api/v1/event/{match_id}/statistics', headers=headers)

        df = pd.DataFrame()
        for i in range(len(response.json()['statistics'][0]['groups'])):
            df_valores = pd.DataFrame(response.json()['statistics'][0]['groups'][i]['statisticsItems'])
            df = pd.concat([df,df_valores])
        df = df[['name', 'home', 'homeValue', 'homeTotal','away', 'awayValue', 'awayTotal']]
        return df
    
    def get_players_match_stats(self, match_url):
        """Returns match data for each player.

        Args:
            match_url (str): Full link to a SofaScore match

        Returns:
            DataFrames: A DataFrame for home and another one for away teams with each row being a player and in each columns a different statistic or data of the player
        """

        headers = self.get_requests_headers()
        match_id = self.get_match_id(match_url)
        
        response = requests.get(f'https://api.sofascore.com/api/v1/event/{match_id}/lineups', headers=headers)

        home_team, away_team = self.get_team_names(match_url)
        names = {'home': home_team, 'away': away_team}

        teams = ['home', 'away']
        dataframes = {}
        for team in teams:
            dataframes[f'df_{team}'] = pd.DataFrame()
            data = pd.DataFrame(response.json()[team]['players'])
            columns_list = [data['player'].apply(pd.Series), data['shirtNumber'], data['jerseyNumber'], data['position'], data['substitute'], data['statistics'].apply(pd.Series), data['captain']]
            dataframes[f'df_{team}'] = pd.concat(columns_list, axis=1)
            dataframes[f'df_{team}']['team'] = names[team]
        
        return dataframes['df_home'], dataframes['df_away']
    
    def get_players_average_positions(self, match_url):
        """Return player averages positions for each team

        Args:
            match_url (str): Full link to a SofaScore match

        Returns:
            DataFrame: Each row is a player and columns averageX and averageY denote their average position on the match.
        """
        match_id = self.get_match_id(match_url)
        headers = self.get_requests_headers()

        response = requests.get(f'https://api.sofascore.com/api/v1/event/{match_id}/average-positions', headers=headers)
        response.json()
        home_team, away_team = self.get_team_names(match_url)
        names = {'home': home_team, 'away': away_team}
        teams = ['home', 'away']
        dataframes = {}
        for team in teams:
            df_team_averages = pd.DataFrame(response.json()[team])
            df_team_averages['team'] = names[team]
            dataframes[f'df_{team}'] = pd.concat([df_team_averages['player'].apply(pd.Series), df_team_averages.drop(columns=['player'])],axis=1)
            
        return dataframes['df_home'], dataframes['df_away']
    
    def get_player_heatmap(self, match_url, player, save_heatmap=True, cmap='OrRd'):
        """Heatmap for a particular player any match.

        Args:
            match_url (str): Full link to a SofaScore match
            player (str): Name of the player (must be the SofaScore one).
            save_heatmap (bool, optional): Save the heatmap generated to a png. Defaults to True.
            cmap (str, optional): Cmap of the kdeplot. Defaults to 'OrRd'.

        Returns:
            fig, ax: Heatmap for any player and fig/axes for further customization
        """
        match_id = self.get_match_id(match_url)
        headers = self.get_requests_headers()

        player_ids = self.get_player_ids(match_url)
        player_id = player_ids[player]

        response = requests.get(f'https://api.sofascore.com/api/v1/event/{match_id}/player/{player_id}/heatmap', headers=headers)
        heatmap = pd.DataFrame(response.json()['heatmap'])

        fig, ax = plt.subplots()

        pitch = Pitch()
        pitch.draw(ax=ax)
        pitch.kdeplot(heatmap.x, heatmap.y,ax=ax,
            levels=100,
            shade=True,
            zorder=-1,
            shade_lowest=True,
            cmap=cmap)
        
        plt.title(f'Heatmap for {player}', size=15, pad=-5)

        plt.gca().invert_yaxis()
        if save_heatmap:
            plt.savefig(f'{player_id}_heatmap.png', bbox_inches='tight')

        return fig, ax
        

        
import pandas as pd
import numpy as np
import warnings
from tqdm import tqdm
from datetime import datetime, timezone, timedelta

from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from .utils import botasaurus_browser_get_json, get_module_comps
from .sofascore_player import SofascorePlayer
from .sofascore_helpers import _get_player_career_stats_df

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

comps = get_module_comps("SOFASCORE")


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
    def _check_and_convert_match_id(self, match: str | int) -> int:
        """ Helper function that will take a Sofascore match URL or match ID and return a match ID

        :param match: Sofascore match URL or match ID
        :type match: str | int
        :raises TypeError: If any of the parameters are the wrong type.
        :rtype: int
        """
        if not isinstance(match, int) and not isinstance(match, str):
            raise TypeError('`match` must a string or int')
        match_id = match if isinstance(match, int) else self.get_match_id_from_url(match)
        return match_id

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """ Returns the valid seasons and their IDs for the given league

        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If any of the parameters are the wrong type.
        :raises InvalidLeagueException: If the league is not valid for this module.
        :return: Available seasons for the league. Season name is key, season ID is value.
        :rtype: dict
        """
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Sofascore', list(comps.keys()))

        url = f'{API_PREFIX}/unique-tournament/{comps[league]["SOFASCORE"]}/seasons/'
        response = botasaurus_browser_get_json(url)
        seasons = dict([(x['year'], x['id']) for x in response['seasons']])
        return seasons

    # ==============================================================================================
    def get_match_dicts(self, year: str, league:str) -> list[dict]:
        """ Returns the matches from the Sofascore API for a given league season.

        :param year: .. include:: ./arg_docstrings/year_sofascore.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If any of the parameters are the wrong type.
        :raises InvalidYearException: If the year is not valid for the league.
        :return: Each element being a single game of the competition
        :rtype: list[dict]
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        matches = list()
        i = 0
        while 1:
            response = botasaurus_browser_get_json(
                f'{API_PREFIX}/unique-tournament/{comps[league]["SOFASCORE"]}/' +
                f'season/{valid_seasons[year]}/events/last/{i}'
            )
            if 'events' not in response:
                break
            matches += response['events']
            i += 1

        return matches

    # ==============================================================================================
    def get_match_id_from_url(self, match_url: str) -> int:
        """ Get match id from a Sofascore match URL.

        This can also be found in the 'id' key of the dict returned from get_match_dict().

        :param match_url: Full link to a SofaScore match
        :type match_url: str
        :raises TypeError: If ``match_url`` is not a string.
        :return: Match ID for a SofaScore match
        :rtype: int
        """
        if not isinstance(match_url, str):
            raise TypeError('`match_url` must be a string.')
        match_id = int(match_url.split('#id:')[-1])
        return match_id

    # ==============================================================================================
    def get_match_url_from_id(self, match_id: str | int) -> str:
        """ Get the Sofascore match URL for a given match ID

        :param match_id: Sofascore match ID
        :type match_id: str | int
        :return: URL to the Sofascore match of the given ID
        :rtype: str
        """
        match_dict = self.get_match_dict(match_id)
        return f"https://www.sofascore.com/{match_dict['homeTeam']['slug']}-" +\
            f"{match_dict['awayTeam']['slug']}/{match_dict['customId']}#id:{match_dict['id']}"

    # ==============================================================================================
    def get_match_dict(self, match_id: str | int) -> dict:
        """ Get match data dict for a single match

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :rtype: dict
        """
        match_id = self._check_and_convert_match_id(match_id)
        response = botasaurus_browser_get_json(f'{API_PREFIX}/event/{match_id}')
        data = response['event']
        return data

    # ==============================================================================================
    def get_team_names(self, match_id: str | int) -> tuple[str, str]:
        """ Get the team names for the home and away teams

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :return: Names of home and away team.
        :rtype: tuple[str, str]
        """
        data = self.get_match_dict(match_id)
        home_team = data['homeTeam']['name']
        away_team = data['awayTeam']['name']
        return home_team, away_team

    # ==============================================================================================
    def get_positions(self, selected_positions: list[str]) -> str:
        """ Returns a string for the parameter filters of the scrape_league_stats() request.

        :param selected_positions: List of the positions available to filter on the
            SofaScore UI
        :type selected_positions: list[str]
        :raises TypeError: If any of the parameters are the wrong type.
        :raises ValueError: If any of the items in ``selected_positions`` are not valid positions.
        :return: Joined abbreviations for the chosen positions
        :rtype: str
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
    def get_match_player_ids(self, match_id: str | int) -> dict:
        """ Get the player IDs for a match

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :return: All players who played in the match. Names are keys, IDs are values.
        :rtype: dict
        """
        match_id = self._check_and_convert_match_id(match_id)
        url = f"{API_PREFIX}/event/{match_id}/lineups"
        response = botasaurus_browser_get_json(url)

        if 'error' not in response:
            teams = ['home', 'away']
            player_ids = dict()
            for team in teams:
                data = response[team]['players']
                for item in data:
                    player_data = item['player']
                    player_ids[player_data['name']] = player_data['id']
        else:
            warnings.warn(
                f"Encountered {response['error']['code']}: {response['error']['message']} from"
                f" {url}. Returning empty dict."
            )
            player_ids = dict()

        return player_ids

    # ==============================================================================================
    def get_league_player_ids(self, year: str, league: str) -> list[int]:
        """ Returns list of player ids for all players in a given year and league

        :param year: .. include:: ./arg_docstrings/year_sofascore.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If any of the parameters are the wrong type.
        :raises InvalidYearException: If the year is not valid for the league.
        :rtype: list[int]
        """
        if not isinstance(year, str):
            raise TypeError("`year` must be a string")
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        url = f"{API_PREFIX}/unique-tournament/{comps[league]['SOFASCORE']}/season/{valid_seasons[year]}/players"
        response = botasaurus_browser_get_json(url)
        player_ids = [x["playerId"] for x in response["players"]]

        return player_ids

    # ==============================================================================================
    def scrape_player_league_stats(
            self, year: str, league: str, accumulation: str='total',
            selected_positions: list[str]=[
                'Goalkeepers', 'Defenders', 'Midfielders', 'Forwards'
            ]
        ) -> pd.DataFrame:
        """ Get every player statistic that can be asked in league pages on Sofascore.

        :param year: .. include:: ./arg_docstrings/year_sofascore.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :param accumulation: Value of the filter accumulation. Can be "per90", "perMatch", or
            "total". Defaults to "total".
        :type accumulation: str
        :param selected_positions: Value of the filter positions. Defaults to
            ["Goalkeepers", "Defenders", "Midfielders", "Forwards"].
        :type selected_positions: list[str]
        :raises TypeError: If any of the parameters are the wrong type.
        :raises InvalidYearException: If the year is not valid for the league.
        :raises ValueError: If ``accumulation`` is not a valid option.
        :rtype: pd.DataFrame
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
        league_id = comps[league]["SOFASCORE"]

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
            response = botasaurus_browser_get_json(request_url)
            results += response['results']
            if (response['page'] == response['pages']) or\
                    (response['pages'] == 0):
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
    def scrape_match_momentum(self, match_id: str | int) -> pd.DataFrame:
        """Get the match momentum values

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :return: Dataframe of match momentum values. Will be empty if the match does not have
            match momentum data.
        :rtype: pd.DataFrame
        """
        match_id = self._check_and_convert_match_id(match_id)
        url = f'{API_PREFIX}/event/{match_id}/graph'
        response = botasaurus_browser_get_json(url)

        if "error" not in response:
            match_momentum_df = pd.DataFrame(response['graphPoints'])
        else:
            warnings.warn(
                f"Encountered {response['error']['code']}: {response['error']['message']} from"
                f" {url}. Returning empty dataframe."
            )
            match_momentum_df = pd.DataFrame()

        return match_momentum_df

    # ==============================================================================================
    def scrape_team_match_stats(self, match_id: str | int) -> pd.DataFrame:
        """ Scrape team stats for a match

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :rtype: pd.DataFrame
        """
        match_id = self._check_and_convert_match_id(match_id)
        url = f'{API_PREFIX}/event/{match_id}/statistics'
        response = botasaurus_browser_get_json(url)

        if "error" not in response:
            df = pd.DataFrame()
            for period in response['statistics']:
                period_name = period['period']
                for group in period['groups']:
                    group_name = group['groupName']
                    temp = pd.DataFrame.from_dict(group['statisticsItems'])
                    temp['period'] = [period_name,] * temp.shape[0]
                    temp['group'] = [group_name,] * temp.shape[0]
                    df = pd.concat([df, temp], ignore_index=True)
        else:
            warnings.warn(
                f"Encountered {response['error']['code']}: {response['error']['message']} from"
                f" {url}. Returning empty dataframe."
            )
            df = pd.DataFrame()

        return df

    # ==============================================================================================
    def scrape_player_match_stats(self, match_id: str | int) -> pd.DataFrame:
        """ Scrape player stats for a match

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :rtype: pd.DataFrame
        """
        match_id = self._check_and_convert_match_id(match_id)
        match_dict = self.get_match_dict(match_id)  # used to get home and away team names and IDs
        url = f'{API_PREFIX}/event/{match_id}/lineups'
        response = botasaurus_browser_get_json(url)

        if "error" not in response:
            home_players = response['home']['players']
            away_players = response['away']['players']
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
            warnings.warn(
                f"Encountered {response['error']['code']}: {response['error']['message']} from"
                f" {url}. Returning empty dataframe."
            )
            df = pd.DataFrame()

        return df

    # ==============================================================================================
    def scrape_player_average_positions(self, match_id: str | int) -> pd.DataFrame:
        """ Return player averages positions for each team

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :return: Each row is a player and columns averageX and averageY denote their average
            position in the match.
        :rtype: pd.DataFrame
        """
        match_id = self._check_and_convert_match_id(match_id)
        home_name, away_name = self.get_team_names(match_id)
        url = f'{API_PREFIX}/event/{match_id}/average-positions'
        response = botasaurus_browser_get_json(url)

        if "error" not in response:
            df = pd.DataFrame()
            for key, name in [('home', home_name), ('away', away_name)]:
                temp = pd.DataFrame(response[key])
                temp['team'] = [name,] * temp.shape[0]
                temp = pd.concat(
                    [temp['player'].apply(pd.Series), temp.drop(columns=['player'])],
                    axis=1
                )
                df = pd.concat([df, temp], axis=0, ignore_index=True)
        else:
            warnings.warn(
                f"Encountered {response['error']['code']}: {response['error']['message']} from"
                f" {url}. Returning empty dataframe."
            )
            df = pd.DataFrame()

        return df

    # ==============================================================================================
    def scrape_heatmaps(self, match_id: str | int) -> dict:
        """ Get the x-y coordinates to create a player heatmap for all players in the match.

        Players who didn't play will have an empty list of coordinates.

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :return: Dict of players, their IDs and their heatmap coordinates, {player name: {'id':
            player_id, 'heatmap': heatmap}, ...}
        :rtype: dict
        """
        match_id = self._check_and_convert_match_id(match_id)
        players = self.get_match_player_ids(match_id)
        for player in players:
            player_id = players[player]
            url = f'{API_PREFIX}/event/{match_id}/player/{player_id}/heatmap'

            response = botasaurus_browser_get_json(url)

            if "error" not in response:
                heatmap = [(z['x'], z['y']) for z in response['heatmap']]
            else:
                # Players that didn't play have empty heatmaps. Don't print warning because there
                # would be a lot of them.
                heatmap = list()

            players[player] = {'id': player_id, 'heatmap': heatmap}

        return players

    # ==============================================================================================
    def scrape_match_shots(self, match_id: str | int) -> pd.DataFrame:
        """ Scrape shots for a match

        :param match_id: Sofascore match URL or match ID
        :type match_id: str | int
        :rtype: pd.DataFrame
        """
        match_id = self._check_and_convert_match_id(match_id)
        url = f"{API_PREFIX}/event/{match_id}/shotmap"
        response = botasaurus_browser_get_json(url)
        if "error" not in response:
            df = pd.DataFrame.from_dict(response["shotmap"])
        else:
            warnings.warn(
                f"Encountered {response['error']['code']}: {response['error']['message']} from"
                f" {url}. Returning empty dataframe."
            )
            df = pd.DataFrame()

        return df

    # ==============================================================================================
    def scrape_team_league_stats(self, year: str, league: str) -> pd.DataFrame:
        """ Get "general" league stats for all teams in the given league year.

        :param year: .. include:: ./arg_docstrings/year_sofascore.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If any of the parameters are the wrong type.
        :raises InvalidYearException: If the year is not valid for the league.
        :rtype: pd.DataFrame
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')

        # Verify year is valid
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons:
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        league_id = comps[league]["SOFASCORE"]
        year_id = valid_seasons[year]

        # Find all teams in the league that season
        teams_list = botasaurus_browser_get_json(
            f"{API_PREFIX}/unique-tournament/{league_id}/season/{year_id}/teams"
        )["teams"]

        # Iterate over teams and build dataframe of stats
        df = pd.DataFrame()
        for team in tqdm(teams_list, desc=f"{year} {league} team stats", ncols=100):
            team_id = team["id"]
            result = botasaurus_browser_get_json(
                f"{API_PREFIX}/team/{team_id}/unique-tournament/{league_id}/season/{year_id}/"
                "statistics/overall"
            )

            if "statistics" in result:
                # Team has league stats, build series with them
                team_stats_dict = result["statistics"]
                team_row = pd.Series(team_stats_dict)
            else:
                # This team has no stats, build an empty series for their row
                team_row = pd.Series()

            # Insert team name and ID into series and convert to DataFrame row
            team_row["teamId"] = team_id
            team_row["teamName"] = team["name"]
            team_row = team_row.to_frame().T

            # Append the team row to the main DataFrame
            df = pd.concat([df, team_row], axis=0, ignore_index=True)

        # Reorder columns so that team name and ID are first
        df = pd.concat(
            [df["teamName"], df["teamId"], df.drop(columns=["teamName", "teamId"])],
            axis=1
        )

        return df

    # ==============================================================================================
    def scrape_player_details(self, year: str, league: str) -> list[SofascorePlayer]:
        """ Scrape details for all players in a given year and league. Details are things like
        name, DOB, position, heigh, weight, contract expiration, etc.

        Please note, the player's team is their current team, not necessarily their team in the
        given year and league.

        :param year: .. include:: ./arg_docstrings/year_sofascore.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :rtype: list[SofascorePlayer]
        """
        player_ids = self.get_league_player_ids(year, league)
        if len(player_ids) == 0:
            print(f"WARNING: No players found for {year} {league}.")

        player_details = list()
        pbar = tqdm(player_ids, ncols=100)
        for player_id in pbar:
            pbar.set_description(f"{year} {league}, player ID {player_id}")

            url = f"{API_PREFIX}/player/{player_id}"
            response = botasaurus_browser_get_json(url)
            player_dict = response["player"]

            player_name = player_dict["name"]
            team_name = player_dict["team"]["name"]
            team_id = player_dict["team"]["id"]
            position = player_dict["position"] if "position" in player_dict else None
            positions_detailed = (
                player_dict["positionsDetailed"] if "positionsDetailed" in player_dict else None
            )
            weight = player_dict["weight"] if "weight" in player_dict else None
            height = player_dict["height"] if "height" in player_dict else None
            # Need to do UNIX time=0 then plus DOB timestamp because sometimes Windows is dumb with
            # negative UNIX timestamps I guess. This should work on all platforms.
            dob = (
                datetime.fromtimestamp(0, timezone.utc)
                + timedelta(seconds=player_dict["dateOfBirthTimestamp"])
                if "dateOfBirthTimestamp" in player_dict else None
            )
            preferred_foot = (
                player_dict["preferredFoot"] if "preferredFoot" in player_dict else None
            )
            country = (
                player_dict["country"]["name"] if "country" in player_dict
                and "name" in player_dict["country"] else None
            )
            contract_until = (
                datetime.fromtimestamp(0, timezone.utc)
                + timedelta(seconds=player_dict["contractUntilTimestamp"])
                if "contractUntilTimestamp" in player_dict else None
            )
            market_value = (
                player_dict["proposedMarketValueRaw"]["value"]
                if "proposedMarketValueRaw" in player_dict
                and "value" in player_dict["proposedMarketValueRaw"] else None
            )
            market_value_currency = (
                player_dict["proposedMarketValueRaw"]["currency"]
                if "proposedMarketValueRaw" in player_dict
                and "currency" in player_dict["proposedMarketValueRaw"] else None
            )
            career_stats = _get_player_career_stats_df(player_id, API_PREFIX)

            player = SofascorePlayer(
                id=player_id, name=player_name, team_name=team_name, team_id=team_id,
                position=position, positions_detailed=positions_detailed, weight=weight,
                height=height, dob=dob, preferred_foot=preferred_foot, country=country,
                contract_until=contract_until, market_value=market_value,
                market_value_currency=market_value_currency, career_stats=career_stats
            )
            player_details.append(player)

        return player_details

from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
import json
import pandas as pd
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import warnings
from ScraperFC.utils import get_module_comps

comps = get_module_comps("UNDERSTAT")

# Understat moved season/league data from embedded <script> tags to AJAX endpoints.
# These headers mimic a browser XHR request, which Understat requires.
_AJAX_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def _ajax_get(url: str, referer: str) -> dict:
    """GET an Understat AJAX endpoint with browser-like headers.

    :param url: Full URL of the AJAX endpoint
    :type url: str
    :param referer: The page URL to send as the HTTP Referer header
    :type referer: str
    :return: Parsed JSON response
    :rtype: dict
    """
    headers = {**_AJAX_HEADERS, "Referer": referer}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def _json_from_script(text: str) -> dict:
    data_str = text.split('JSON.parse(\'')[1].split('\')')[0].encode('utf-8').decode('unicode_escape')
    data_dict = json.loads(data_str)
    return data_dict


class Understat:

    # ==============================================================================================
    def get_season_link(self, year: str, league: str) -> str:
        """ Gets Understat URL of the chosen league season.

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If any of the parameters are the wrong type
        :raises InvalidLeagueException: If the league is not a valid league for this module.
        :raises InvalidYearException: If the year is not a valid year for this league.
        :return: URL to the Understat page of the chosen league season.
        :rtype: str
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Understat', list(comps.keys()))
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons:
            raise InvalidYearException(year, league, valid_seasons)

        return f'{comps[league]["UNDERSTAT"]}/{year.split("/")[0]}'

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> list[str]:
        """ Returns valid season strings for the chosen league.

        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises InvalidLeagueException: If the league is not a valid league for this module.
        :return: List of valid year strings for this league
        :rtype: list[str]
        """
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Understat', list(comps.keys()))

        soup = BeautifulSoup(requests.get(comps[league]["UNDERSTAT"]).content, 'html.parser')
        valid_season_tags = soup.find('select', {'name': 'season'}).find_all('option')  # type: ignore
        valid_seasons = [x.text for x in valid_season_tags]
        return valid_seasons

    # ==============================================================================================
    def get_match_links(self, year: str, league: str) -> list[str]:
        """ Gets all of the match links for the chosen league season

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: List of match links of the chosen league season
        :rtype: list[str]
        """
        matches_data, _, _ = self.scrape_season_data(year, league)
        return [f'https://understat.com/match/{x["id"]}' for x in matches_data if x['isResult']]

    # ==============================================================================================
    def get_team_links(self, year: str, league: str) -> list[str]:
        """ Gets all of the team links for the chosen league season

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: List of team links of the chosen league season
        :rtype: list[str]
        """
        _, teams_data, _ = self.scrape_season_data(year, league)
        return [
            f'https://understat.com/team/{x["title"].replace(" ", "_")}/{year.split("/")[0]}'
            for x in teams_data.values()
        ]

    # ==============================================================================================
    def scrape_season_data(self, year: str, league: str) -> tuple[list, dict, list]:
        """ Scrapes data for chosen Understat league season.

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: Tuple of (matches_data, teams_data, players_data)
        :rtype: tuple[list, dict, list]
        """
        season_link = self.get_season_link(year, league)

        # Understat previously embedded datesData/teamsData/playersData directly
        # in <script> tags on the league page. They now serve this data via an
        # AJAX endpoint. The league code lives at the end of the season URL
        # (e.g. "EPL" from "https://understat.com/league/EPL/2024").
        league_code = season_link.split('/')[-2]
        season_year = year.split('/')[0]
        ajax_url = f'https://understat.com/getLeagueData/{league_code}/{season_year}'

        data = _ajax_get(ajax_url, referer=season_link)

        matches_data = data['dates']    # list of match dicts (formerly datesData)
        teams_data   = data['teams']    # dict of team dicts  (formerly teamsData)
        players_data = data['players']  # list of player dicts (formerly playersData)

        return matches_data, teams_data, players_data

    # ==============================================================================================
    def scrape_league_tables(self, year: str, league: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """ Scrapes the league table for the chosen league season.

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: Tuple of league table, home table, and away table DataFrames
        :rtype: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        """
        _, teams_data, _ = self.scrape_season_data(year, league)

        df = pd.DataFrame()
        for x in teams_data.values():
            # Create matches df for each team
            matches = pd.DataFrame.from_dict(x['history'])
            newcols = list()
            for c in matches.columns:
                if isinstance(matches.loc[0, c], dict):
                    newcols.append(matches[c].apply(pd.Series).add_prefix(f'{c}_'))
                else:
                    newcols.append(matches[c])  # type: ignore
            matches = pd.concat(newcols, axis=1)
            matches['id'] = [x['id'],] * matches.shape[0]
            matches['title'] = [x['title'],] * matches.shape[0]
            df = pd.concat([df, matches], axis=0, ignore_index=True)

        # Rename columns to match Understat
        colmapping = {
            'title': 'Team', 'wins': 'W', 'draws': 'D', 'loses': 'L', 'scored': 'G', 'missed': 'GA',
            'pts': 'PTS', 'npxG': 'NPxG', 'npxGA': 'NPxGA', 'npxGD': 'NPxGD', 'deep': 'DC',
            'deep_allowed': 'ODC', 'xpts': 'xPTS',
        }
        df = df.rename(columns=colmapping)

        # Added matches played column
        df['M'] = df['W'] + df['D'] + df['L']

        # Create initiial league, home, and away tables
        lg_tbl = df.groupby('Team', as_index=False).sum()\
            .sort_values('PTS', ascending=False).reset_index(drop=True)
        h_tbl = df[df['h_a'] == 'h'].groupby('Team', as_index=False).sum()\
            .sort_values('PTS', ascending=False).reset_index(drop=True)
        a_tbl = df[df['h_a'] == 'a'].groupby('Team', as_index=False).sum()\
            .sort_values('PTS', ascending=False).reset_index(drop=True)

        # Now compute PPDA columns, doing this before groupby().sum() leads to inaccurate values
        lg_tbl['PPDA'] = lg_tbl['ppda_att'] / lg_tbl['ppda_def']
        lg_tbl['OPPDA'] = lg_tbl['ppda_allowed_att'] / lg_tbl['ppda_allowed_def']

        h_tbl['PPDA'] = h_tbl['ppda_att'] / h_tbl['ppda_def']
        h_tbl['OPPDA'] = h_tbl['ppda_allowed_att'] / h_tbl['ppda_allowed_def']

        a_tbl['PPDA'] = a_tbl['ppda_att'] / a_tbl['ppda_def']
        a_tbl['OPPDA'] = a_tbl['ppda_allowed_att'] / a_tbl['ppda_allowed_def']

        # Drop columns
        dropcols = ['ppda_att', 'ppda_def', 'ppda_allowed_att', 'ppda_allowed_def']
        lg_tbl.drop(columns=dropcols)
        h_tbl.drop(columns=dropcols)
        a_tbl.drop(columns=dropcols)

        # Reorder columns to match Understat
        ordered_cols = [
            'Team', 'M', 'W', 'D', 'L', 'G', 'GA', 'PTS', 'xG', 'NPxG', 'xGA', 'NPxGA', 'NPxGD',
            'PPDA', 'OPPDA', 'DC', 'ODC', 'xPTS'
        ]
        lg_tbl = lg_tbl[ordered_cols]
        h_tbl = h_tbl[ordered_cols]
        a_tbl = a_tbl[ordered_cols]

        return lg_tbl, h_tbl, a_tbl

    # ==============================================================================================
    def scrape_match(self, link: str, as_df: bool = False) -> tuple[dict | pd.DataFrame, dict | pd.DataFrame, dict | pd.DataFrame]:
        """ Scrapes a single match from Understat.

        :param link: URL to the match
        :type link: str
        :param as_df: If True, will return the data as DataFrames. If False, data will be
            returned as dicts. Defaults to False.
        :type as_df: bool
        :raises TypeError: If any of the parameters are the wrong type
        :return: Tuple of (shots_data, match_info, rosters_data)
        :rtype: tuple[dict | pd.DataFrame, dict | pd.DataFrame, dict | pd.DataFrame]
        """
        if not isinstance(link, str):
            raise TypeError('`link` must be a string.')
        if not isinstance(as_df, bool):
            raise TypeError('`as_df` must be a boolean.')

        match_id = link.rstrip('/').split('/')[-1]
        ajax_url = f'https://understat.com/getMatchData/{match_id}'

        try:
            data = _ajax_get(ajax_url, referer=link)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                warnings.warn(f"404 error for {link}. Returning empty dicts/DataFrames.")
                if as_df:
                    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()  # type: ignore
                else:
                    return dict(), dict(), dict()  # type: ignore
            raise

        shots_data = data['shots']    # dict with 'h' and 'a' shot lists
        rosters_data = data['rosters']  # dict with 'h' and 'a' player dicts

        # Reconstruct match_info from shot records — each shot carries team names,
        # scores, and date, so any shot gives us the full match context.
        all_shots = shots_data.get('h', []) + shots_data.get('a', [])
        if all_shots:
            s = all_shots[0]
            match_info: dict = {
                'h_team': s.get('h_team'), 'a_team': s.get('a_team'),
                'h_goals': s.get('h_goals'), 'a_goals': s.get('a_goals'),
                'date': s.get('date'), 'match_id': s.get('match_id'),
            }
        else:
            match_info = {}

        if as_df:
            shots_data = pd.DataFrame(all_shots)  # type: ignore
            match_info = pd.Series(match_info).to_frame().T  # type: ignore
            rosters_data = pd.DataFrame(  # type: ignore
                list(rosters_data.get('h', {}).values()) + list(rosters_data.get('a', {}).values())
            )

        return shots_data, match_info, rosters_data

    # ==============================================================================================
    def scrape_matches(self, year: str, league: str, as_df: bool = False) -> dict:
        """ Scrapes all of the matches from the chosen league season.

        Gathers all match links from the chosen league season and then calls scrape_match() on each
        one.

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :param as_df: If True, the data for each match will be returned as DataFrames. If False,
            individual match data will be returned as dicts. Defaults to False.
        :type as_df: bool
        :return: Dictionary of match data, where each key is a match link and the value is a dict
            of match data.
        :rtype: dict
        """
        links = self.get_match_links(year, league)

        matches = dict()
        for link in tqdm(links, desc=f'{year} {league} matches'):
            shots, info, rosters = self.scrape_match(link, as_df)
            matches[link] = {'shots_data': shots, 'match_info': info, 'rosters_data': rosters}

        return matches

    # ==============================================================================================
    def scrape_team_data(self, team_link: str, as_df: bool = False) -> tuple[dict | pd.DataFrame, dict | pd.DataFrame, dict | pd.DataFrame]:
        """ Scrapes team data from a team's Understat link

        Note that for Understat, team links are season-specific.

        :param team_link: URL to the team's Understat page
        :type team_link: str
        :param as_df: If True, data will be returned as dataframes. If False, dicts. Defaults
            to False.
        :type as_df: bool
        :return: Tuple of (matches_data, team_data, player_data)
        :raises TypeError: If any of the parameters are the wrong type
        :rtype: tuple[dict | pd.DataFrame, dict | pd.DataFrame, dict | pd.DataFrame]
        """
        if not isinstance(team_link, str):
            raise TypeError('`team_link` must be a string.')
        if not isinstance(as_df, bool):
            raise TypeError('`as_df` must be a boolean.')

        # Team URL format: https://understat.com/team/{TeamName}/{year}
        parts = team_link.rstrip('/').split('/')
        team_name, season_year = parts[-2], parts[-1]
        ajax_url = f'https://understat.com/getTeamData/{team_name}/{season_year}'

        data = _ajax_get(ajax_url, referer=team_link)

        matches_data = data['dates']       # list of match dicts (formerly datesData)
        team_data    = data['statistics']  # dict of stat categories (formerly statisticsData)
        player_data  = data['players']     # list of player dicts (formerly playersData)

        if as_df:
            matches_data = pd.DataFrame.from_dict(matches_data)  # type: ignore
            newcols = list()
            for c in matches_data.columns:  # type: ignore
                if isinstance(matches_data.loc[0, c], dict):  # type: ignore
                    newcols.append(matches_data[c].apply(pd.Series).add_prefix(f'{c}_'))
                else:
                    newcols.append(matches_data[c])  # type: ignore
            matches_data = pd.concat(newcols, axis=1)

            for key, value in team_data.items():
                table = list()
                for k, v in value.items():
                    # Drop against because it contains dicts
                    temp = pd.DataFrame.from_dict([v,]).drop(columns='against')  # type: ignore
                    # Make the against dict into it's own DF and the concat it to temp
                    temp = pd.concat(
                        [
                            temp,
                            pd.DataFrame.from_dict([v['against'],]).add_suffix('_against')  # type: ignore
                        ],
                        axis=1
                    )
                    temp['stat'] = [k,]
                    table.append(temp)
                team_data[key] = pd.concat(table, axis=0, ignore_index=True)

            player_data = pd.DataFrame.from_dict(player_data)  # type: ignore

        return matches_data, team_data, player_data

    # ==============================================================================================
    def scrape_all_teams_data(self, year: str, league: str, as_df: bool = False) -> dict:
        """ Scrapes data for all teams in the given league season.

        :param year: .. include:: ./arg_docstrings/year_understat.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :param as_df: If True, each team's data will be returned as dataframes. If False,
            return dicts. Defaults to False.
        :type as_df: bool
        :return: Dictionary of team data, where each key is a team link and the value is a dict of
            team data.
        :rtype: dict
        """
        team_links = self.get_team_links(year, league)
        return_package = dict()
        for team_link in tqdm(team_links, desc=f'{year} {league} teams'):
            matches, team, players = self.scrape_team_data(team_link, as_df)
            return_package[team_link] = {
                'matches': matches, 'team_data': team, 'players_data': players
            }
        return return_package

    # ==============================================================================================
    def scrape_shot_xy(self, year: str, league: str, as_df: bool = False) -> None:
        """ Deprecated. Use `scrape_matches()` instead.
        """
        raise NotImplementedError(
            'Deprecated. This data is included in the output of `scrape_matches()` now.'
        )

    # ==============================================================================================
    def scrape_home_away_tables(self, year: str, league: str, normalize: bool = False) -> None:
        """ Deprecated. Use `scrape_league_tables()` instead.
        """
        raise NotImplementedError(
            'Deprecated. Home and away tables are output by `scrape_league_tables()` now.'
        )

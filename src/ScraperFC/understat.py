from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
import json
import pandas as pd
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import warnings
from typing import Sequence, Union

comps = {
    'EPL': 'https://understat.com/league/EPL',
    'La Liga': 'https://understat.com/league/La_liga',
    'Bundesliga': 'https://understat.com/league/Bundesliga',
    'Serie A': 'https://understat.com/league/Serie_A',
    'Ligue 1': 'https://understat.com/league/Ligue_1',
    'RFPL': 'https://understat.com/league/RFPL'
}


def _json_from_script(text: str) -> dict:
    data_str = text.split('JSON.parse(\'')[1].split('\')')[0].encode('utf-8').decode('unicode_escape')
    data_dict = json.loads(data_str)
    return data_dict


class Understat:
        
    # ==============================================================================================
    def get_season_link(self, year: str, league: str) -> str:
        """ Gets Understat URL of the chosen league season.

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.
        
        Returns
        -------
        : str
            URL to the Understat page of the chosen league season.
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
        
        return f'{comps[league]}/{year.split("/")[0]}'
    
    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> Sequence[str]:
        """ Returns valid season strings for the chosen league.

        Parameters
        ----------
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.
        
        Returns
        ------
        : list of str
            Valid seasons for the chosen league
        """
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Understat', list(comps.keys()))
        
        soup = BeautifulSoup(requests.get(comps[league]).content, 'html.parser')
        valid_season_tags = soup.find('select', {'name': 'season'}).find_all('option')  # type: ignore
        valid_seasons = [x.text for x in valid_season_tags]
        return valid_seasons
        
    # ==============================================================================================
    def get_match_links(self, year: str, league: str) -> Sequence[str]:
        """ Gets all of the match links for the chosen league season

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.

        Returns
        -------
        : list of str
            List of match links of the chosen league season
        """
        matches_data, _, _ = self.scrape_season_data(year, league)
        return [f'https://understat.com/match/{x["id"]}' for x in matches_data if x['isResult']]
    
    # ==============================================================================================
    def get_team_links(self, year: str, league: str) -> Sequence[str]:
        """ Gets all of the team links for the chosen league season

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.

        Returns
        -------
        : list of str
            List of team URL's from the chosen season.
        """
        _, teams_data, _ = self.scrape_season_data(year, league)
        return [
            f'https://understat.com/team/{x["title"].replace(" ", "_")}/{year.split("/")[0]}'
            for x in teams_data.values()
        ]

    # ==============================================================================================
    def scrape_season_data(self, year: str, league: str) -> Sequence[dict]:
        """ Scrapes data for chosen Understat league season.

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.

        Returns
        -------
        : tuple of dicts
            matches_data, teams_data, players_data
        """
        season_link = self.get_season_link(year, league)
        soup = BeautifulSoup(requests.get(season_link).content, 'html.parser')

        scripts = soup.find_all('script')
        dates_data_tag = [x for x in scripts if 'datesData' in x.text][0]
        teams_data_tag = [x for x in scripts if 'teamsData' in x.text][0]
        players_data_tag = [x for x in scripts if 'playersData' in x.text][0]

        matches_data = _json_from_script(dates_data_tag.text)
        teams_data = _json_from_script(teams_data_tag.text)
        players_data = _json_from_script(players_data_tag.text)

        return matches_data, teams_data, players_data
          
    # ==============================================================================================
    def scrape_league_tables(self, year: str, league: str) -> Sequence[pd.DataFrame]:
        """ Scrapes the league table for the chosen league season.

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.

        Returns
        -------
        : tuple of DataFrames
            League table, home table, away table
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
    def scrape_match(self, link: str, as_df: bool = False) -> Sequence[Union[dict, pd.DataFrame]]:
        """ Scrapes a single match from Understat.

        Parameters
        ----------
        link : str
            URL to the match
        as_df : bool, optional, default False
            If True, will return the data as DataFrames. If False, data will be returned as dicts.

        Returns
        -------
        : tuple of dicts or DataFrames
            shots_data, match_info (match stats), rosters_data (player data)
        """
        if not isinstance(link, str):
            raise TypeError('`link` must be a string.')
        if not isinstance(as_df, bool):
            raise TypeError('`as_df` must be a boolean.')
        
        r = requests.get(link)
        if r.status_code == 404:
            warnings.warn(f"404 error for {link}. Returning empty dicts/DataFrames.")
            if as_df:
                shots_data, match_info, rosters_data = pd.DataFrame(), pd.DataFrame(), \
                    pd.DataFrame()  # type: ignore
            else:
                shots_data, match_info, rosters_data = dict(), dict(), dict()   # type: ignore
        else:
            soup = BeautifulSoup(r.content, 'html.parser')

            scripts = soup.find_all('script')
            shots_data_tag = [x for x in scripts if 'shotsData' in x.text][0]
            # 2024-06-20 Match info is actually in the shots data tag but have this line separate
            # in case that changes in the future.
            match_info_tag = [x for x in scripts if 'match_info' in x.text][0]
            rosters_data_tag = [x for x in scripts if 'rostersData' in x.text][0]

            shots_data = _json_from_script(shots_data_tag.text.split('match_info')[0])  # type: ignore
            match_info = _json_from_script(match_info_tag.text.split('match_info')[1])  # type: ignore
            rosters_data = _json_from_script(rosters_data_tag.text)  # type: ignore

            if as_df:
                shots_data = pd.DataFrame.from_dict(shots_data['h'] + shots_data['a'])   # type: ignore
                match_info = pd.Series(match_info).to_frame().T     # type: ignore
                rosters_data = pd.DataFrame.from_dict(
                    list(rosters_data['h'].values()) + list(rosters_data['a'].values())    # type: ignore
                )   # type: ignore
        
        return shots_data, match_info, rosters_data

    # ==============================================================================================
    def scrape_matches(self, year: str, league: str, as_df: bool = False) -> dict:
        """ Scrapes all of the matches from the chosen league season.
        
        Gathers all match links from the chosen league season and then calls scrape_match() on each
        one.

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.
        as_df : bool, optional, default False
            If True, the data for each match will be returned as DataFrames. If False, invdividual
            match data will be dicts.

        Returns
        -------
        : dict
            {link: {'shots_data': shots, 'match_info': info, 'rosters_data': rosters}, ...}
        """
        links = self.get_match_links(year, league)
        
        matches = dict()
        for link in tqdm(links, desc=f'{year} {league} matches'):
            shots, info, rosters = self.scrape_match(link, as_df)
            matches[link] = {'shots_data': shots, 'match_info': info, 'rosters_data': rosters}
        
        return matches

    # ==============================================================================================
    def scrape_team_data(self, team_link: str, as_df: bool = False) -> Sequence:
        """ Scrapes team data from a team's Understat link
        
        Note that for Understat, team links are season-specific.
        
        Parameters
        ----------
        team_link : str

        as_df : bool, optional, default False
            If True, data will be returned as DataFrames. If False, dicts.
            
        Returns
        -------
        : tuple
            matches, team_data, player_data
        """
        if not isinstance(team_link, str):
            raise TypeError('`team_link` must be a string.')
        if not isinstance(as_df, bool):
            raise TypeError('`as_df` must be a boolean.')

        scripts = BeautifulSoup(requests.get(team_link).content, 'html.parser').find_all('script')

        dates_data_tag = [x for x in scripts if 'datesData' in x.text][0]
        stats_data_tag = [x for x in scripts if 'statisticsData' in x.text][0]
        player_data_tag = [x for x in scripts if 'playersData' in x.text][0]

        matches_data = _json_from_script(dates_data_tag.text)
        team_data = _json_from_script(stats_data_tag.text)
        player_data = _json_from_script(player_data_tag.text)

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

        Parameters
        ----------
        year : str
            See the :ref:`understat_year` `year` parameter docs for details.
        league : str
            League. Look in ScraperFC.Understat comps variable for available leagues.
        as_df : bool, optional, default False
            If True, each team's data will be returned as DataFrames. If False, dicts.

        Returns
        -------
        : dict
            {team_link: {'matches': match data, 'team_data': team stats, 'players_data':
            player stats}, ...}
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

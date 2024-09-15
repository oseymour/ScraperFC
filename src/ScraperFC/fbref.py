from bs4 import BeautifulSoup
import requests
from .scraperfc_exceptions import InvalidYearException, InvalidLeagueException, \
    NoMatchLinksException, FBrefRateLimitException
import time
import numpy as np
import pandas as pd
from io import StringIO
import re
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import Sequence, Union

stats_categories = {
    'standard': {'url': 'stats', 'html': 'standard'},
    'goalkeeping': {'url': 'keepers', 'html': 'keeper'},
    'advanced goalkeeping': {'url': 'keepersadv', 'html': 'keeper_adv'},
    'shooting': {'url': 'shooting', 'html': 'shooting'},
    'passing': {'url': 'passing', 'html': 'passing'},
    'pass types': {'url': 'passing_types', 'html': 'passing_types'},
    'goal and shot creation': {'url': 'gca', 'html': 'gca'},
    'defensive': {'url': 'defense', 'html': 'defense'},
    'possession': {'url': 'possession', 'html': 'possession'},
    'playing time': {'url': 'playingtime', 'html': 'playing_time'},
    'misc': {'url': 'misc', 'html': 'misc'}
}

comps = {
    # Men's club international cups
    'Copa Libertadores': {
        'history url': 'https://fbref.com/en/comps/14/history/Copa-Libertadores-Seasons',
        'finders': ['Copa-Libertadores']},
    'Champions League': {
        'history url': 'https://fbref.com/en/comps/8/history/Champions-League-Seasons',
        'finders': ['European-Cup', 'Champions-League']},
    'Europa League': {
        'history url': 'https://fbref.com/en/comps/19/history/Europa-League-Seasons',
        'finders': ['UEFA-Cup', 'Europa-League']},
    'Europa Conference League': {
        'history url': 'https://fbref.com/en/comps/882/history/Europa-Conference-League-Seasons',
        'finders': ['Europa-Conference-League']},
    # Men's national team competitions
    'World Cup': {
        'history url': 'https://fbref.com/en/comps/1/history/World-Cup-Seasons',
        'finders': ['World-Cup']},
    'Copa America': {
        'history url': 'https://fbref.com/en/comps/685/history/Copa-America-Seasons',
        'finders': ['Copa-America']},
    'Euros': {
        'history url': 'https://fbref.com/en/comps/676/history/European-Championship-Seasons',
        'finders': ['UEFA-Euro', 'European-Championship']},
    # Men's big 5
    'Big 5 combined': {
        'history url': 'https://fbref.com/en/comps/Big5/history/Big-5-European-Leagues-Seasons',
        'finders': ['Big-5-European-Leagues']},
    'EPL': {
        'history url': 'https://fbref.com/en/comps/9/history/Premier-League-Seasons',
        'finders': ['Premier-League', 'First-Division']},
    'Ligue 1': {
        'history url': 'https://fbref.com/en/comps/13/history/Ligue-1-Seasons',
        'finders': ['Ligue-1', 'Division-1']},
    'Bundesliga': {
        'history url': 'https://fbref.com/en/comps/20/history/Bundesliga-Seasons',
        'finders': ['Bundesliga']},
    'Serie A': {
        'history url': 'https://fbref.com/en/comps/11/history/Serie-A-Seasons',
        'finders': ['Serie-A']},
    'La Liga': {
        'history url': 'https://fbref.com/en/comps/12/history/La-Liga-Seasons',
        'finders': ['La-Liga']},
    # Men's domestic leagues - 1st tier
    'MLS': {
        'history url': 'https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons',
        'finders': ['Major-League-Soccer']},
    'Brazilian Serie A': {
        'history url': 'https://fbref.com/en/comps/24/history/Serie-A-Seasons',
        'finders': ['Serie-A']},
    'Eredivisie': {
        'history url': 'https://fbref.com/en/comps/23/history/Eredivisie-Seasons',
        'finders': ['Eredivisie']},
    'Liga MX': {
        'history url': 'https://fbref.com/en/comps/31/history/Liga-MX-Seasons',
        'finders': ['Primera-Division', 'Liga-MX']},
    'Primeira Liga': {
        'history url': 'https://fbref.com/en/comps/32/history/Primeira-Liga-Seasons',
        'finders': ['Primeira-Liga']},
    'Belgian Pro League': {
        'history url': 'https://fbref.com/en/comps/37/history/Belgian-Pro-League-Seasons',
        'finders': ['Belgian-Pro-League', 'Belgian-First-Division']},
    'Argentina Liga Profesional': {
        'history url': 'https://fbref.com/en/comps/21/history/Primera-Division-Seasons',
        'finders': ['Primera-Division']},
    # Men's domestic league - 2nd tier
    'EFL Championship': {
        'history url': 'https://fbref.com/en/comps/10/history/Championship-Seasons',
        'finders': ['First-Division', 'Championship']},
    'La Liga 2': {
        'history url': 'https://fbref.com/en/comps/17/history/Segunda-Division-Seasons',
        'finders': ['Segunda-Division']},
    '2. Bundesliga': {
        'history url': 'https://fbref.com/en/comps/33/history/2-Bundesliga-Seasons',
        'finders': ['2-Bundesliga']},
    'Ligue 2': {
        'history url': 'https://fbref.com/en/comps/60/history/Ligue-2-Seasons',
        'finders': ['Ligue-2']},
    'Serie B': {
        'history url': 'https://fbref.com/en/comps/18/history/Serie-B-Seasons',
        'finders': ['Serie-B']},
    # Women's internation club competitions
    'Womens Champions League': {
        'history url': 'https://fbref.com/en/comps/181/history/Champions-League-Seasons',
        'finders': ['Champions-League']},
    # Women's national team competitions
    'Womens World Cup': {
        'history url': 'https://fbref.com/en/comps/106/history/Womens-World-Cup-Seasons',
        'finders': ['Womens-World-Cup']},
    'Womens Euros': {
        'history url': 'https://fbref.com/en/comps/162/history/UEFA-Womens-Euro-Seasons',
        'finders': ['UEFA-Womens-Euro']},
    # Women's domestic leagues
    'NWSL': {
        'history url': 'https://fbref.com/en/comps/182/history/NWSL-Seasons',
        'finders': ['NWSL']},
    'A-League Women': {
        'history url': 'https://fbref.com/en/comps/196/history/A-League-Women-Seasons',
        'finders': ['A-League-Women', 'W-League']},
    'WSL': {
        'history url': 'https://fbref.com/en/comps/189/history/Womens-Super-League-Seasons',
        'finders': ['Womens-Super-League']},
    'D1 Feminine': {
        'history url': 'https://fbref.com/en/comps/193/history/Division-1-Feminine-Seasons',
        'finders': ['Division-1-Feminine']},
    'Womens Bundesliga': {
        'history url': 'https://fbref.com/en/comps/183/history/Frauen-Bundesliga-Seasons',
        'finders': ['Frauen-Bundesliga']},
    'Womens Serie A': {
        'history url': 'https://fbref.com/en/comps/208/history/Serie-A-Seasons',
        'finders': ['Serie-A']},
    'Liga F': {
        'history url': 'https://fbref.com/en/comps/230/history/Liga-F-Seasons',
        'finders': ['Liga-F']},
    # Women's domestic cups
    'NWSL Challenge Cup': {
        'history url': 'https://fbref.com/en/comps/881/history/NWSL-Challenge-Cup-Seasons',
        'finders': ['NWSL-Challenge-Cup']},
    'NWSL Fall Series': {
        'history url': 'https://fbref.com/en/comps/884/history/NWSL-Fall-Series-Seasons',
        'finders': ['NWSL-Fall-Series']},
}


class FBref():

    # ==============================================================================================
    def __init__(self, wait_time: int=7) -> None:
        # FBref rate limits bots -- https://www.sports-reference.com/bot-traffic.html
        self.wait_time = wait_time

    # ==============================================================================================
    def _driver_init(self) -> None:
        """ Private, creates a headless selenium webdriver
        """
        options = Options()
        options.add_argument('--incognito')
        options.add_argument('--headless')
        prefs = {'profile.managed_default_content_settings.images': 2}  # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options)

    # ==============================================================================================
    def _driver_close(self) -> None:
        """ Private, closes the Selenium webdriver
        """
        self.driver.close()
        self.driver.quit()

    # ==============================================================================================
    def _get(self, url: str) -> requests.Response:
        """ Private, calls requests.get() and enforces FBref's wait time.
        """
        response = requests.get(url)
        time.sleep(self.wait_time)
        if response.status_code == 429:
            raise FBrefRateLimitException()
        return response

    # ==============================================================================================
    def _driver_get(self, url: str) -> None:
        """ Private, calls driver.get() and enforces FBref's wait time.
        """
        self.driver.get(url)
        time.sleep(self.wait_time)
        if "429 error" in self.driver.page_source:
            self._driver_close()
            raise FBrefRateLimitException()

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """ Finds all of the valid years and their URLs for a given competition

        Parameters
        ----------
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        Returns
        -------
        : dict
            {year: URL, ...}, URLs need to be appended to "https://fbref.com" to be a complete URL.
        """
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'FBref', list(comps.keys()))

        url = comps[league]['history url']  # type: ignore
        r = self._get(url)  # type: ignore
        soup = BeautifulSoup(r.content, 'html.parser')

        season_urls = dict([
            (x.text, x.find('a')['href'])
            for x in soup.find_all('th', {'data-stat': True, 'class': True})
            if x.find('a') is not None
        ])

        return season_urls

    # ==============================================================================================
    def get_season_link(self, year: str, league: str) -> str:
        """ Returns the URL for the chosen league season.

        Parameters
        ----------
        year : str
            See the :ref:`fbref_year` `year` parameter docs for details.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        Returns
        -------
        : str
            URL to the FBref page of the chosen league season
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'FBref', list(comps.keys()))

        seasons = self.get_valid_seasons(league)

        if year not in seasons:
            raise InvalidYearException(year, league, list(seasons.keys()))

        return 'https://fbref.com/' + seasons[year]

    # ==============================================================================================
    def get_match_links(self, year: str, league: str) -> Sequence[str]:
        """ Gets all match links for the chosen league season.

        Parameters
        ----------
        year : str
            See the :ref:`fbref_year` `year` parameter docs for details.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        Returns
        -------
        : list of str
            FBref links to all matches for the chosen league season
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'FBref', list(comps.keys()))
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons:
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        season_link = self.get_season_link(year, league)

        # Get the Scores and Fixtures page
        split = season_link.split('/')
        split.insert(-1, 'schedule')
        split[-1] = '-'.join(split[-1].split('-')[:-1]) + '-Scores-and-Fixtures'
        fixtures_url = '/'.join(split)

        soup = BeautifulSoup(self._get(fixtures_url).content, 'html.parser')

        # Identify match links
        match_urls = list()
        possible_els = soup.find_all('td', {'class': True, 'data-stat': True})
        if len(possible_els) == 0:
            raise NoMatchLinksException(year, league, fixtures_url)
        for x in possible_els:
            a = x.find('a')
            if (a is not None
                    and 'match' in a['href']
                    and np.any([f in a['href'] for f in comps[league]['finders']])):
                match_urls.append('https://fbref.com' + a['href'])
        match_urls = list(set(match_urls))
        return match_urls

    # ==============================================================================================
    def scrape_league_table(self, year: str, league: str) -> Sequence[pd.DataFrame]:
        """ Scrapes the league table of the chosen league season

        Parameters
        ----------
        year : str
            See the :ref:`fbref_year` `year` parameter docs for details.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        Returns
        -------
        : list of DataFrame
            Returns a list of all position tables from the league's homepage on
            FBref. The first table will be the league table, all tables after that
            vary by competition.
        """
        season_link = self.get_season_link(year, league)
        tables = list()
        for df in pd.read_html(season_link):
            if 'Rk' in df.columns:
                # Remove all-NaN rows
                df = df.dropna(axis=0, how='all').reset_index(drop=True)

                # Add the df to tables
                tables.append(df)
        return tables

    # ==============================================================================================
    def scrape_match(self, link: str) -> pd.DataFrame:
        """ Scrapes an FBref match page.

        Parameters
        ----------
        link : str
            URL to the FBref match page
        Returns
        -------
        : DataFrame
            DataFrame containing most parts of the match page if they're available (e.g. formations,
            lineups, scores, player stats, etc.). The fields that are available vary by competition
            and year.
        """
        if not isinstance(link, str):
            raise TypeError('`link` must be a string.')

        r = self._get(link)
        soup = BeautifulSoup(r.content, 'html.parser')

        # General match info
        date = soup.find("div", {"class": "scorebox_meta"}).find("strong").text  # type: ignore
        stage = soup.find("div", {"role": "main"}).find("div").text  # type: ignore

        # Team names, IDs, goals, and xG
        team_els = soup.find("div", {"class": "scorebox"}).find_all("div", recursive=False)  # type: ignore
        home_el, away_el = team_els[0], team_els[1]

        home_name = home_el.find("div").text.strip()
        home_id = home_el.find("div").find("strong").find("a")["href"].split("/")[3]
        home_goals = int(home_el.find("div", {"class": "score"}).text)

        away_name = away_el.find("div").text.strip()
        away_id = away_el.find("div").find("strong").find("a")["href"].split("/")[3]
        away_goals = int(away_el.find("div", {"class": "score"}).text)

        # Outfield player stats tables
        home_player_stats_tag, away_player_stats_tag = soup.find_all(
            "div", {"id": re.compile("all_player_stats")}
        )
        home_player_stats_table_tags = home_player_stats_tag\
            .find_all("table", re.compile("stats_"))
        away_player_stats_table_tags = away_player_stats_tag\
            .find_all("table", re.compile("stats_"))

        home_player_stats_dict = dict()
        for table_tag in home_player_stats_table_tags:
            table_name = " ".join(table_tag["id"].split("_")[2:]).capitalize()
            table_df = pd.read_html(StringIO(str(table_tag)))[0]
            home_player_stats_dict[table_name] = table_df

        away_player_stats_dict = dict()
        for table_tag in away_player_stats_table_tags:
            table_name = " ".join(table_tag["id"].split("_")[2:]).capitalize()
            table_df = pd.read_html(StringIO(str(table_tag)))[0]
            away_player_stats_dict[table_name] = table_df

        # Keeper stats tables
        # Do home and away separately because some matches only have GK stats for 1 team
        home_gk_table_tag = soup.find("table", {"id": re.compile(f"keeper_stats_{home_id}")})
        if home_gk_table_tag:
            home_gk_df = pd.read_html(StringIO(str(home_gk_table_tag)))[0]
            home_player_stats_dict["Keeper"] = home_gk_df
        else:
            home_player_stats_dict["Keeper"] = None  # type: ignore
        
        away_gk_table_tag = soup.find("table", {"id": re.compile(f"keeper_stats_{away_id}")})
        if away_gk_table_tag:
            away_gk_df = pd.read_html(StringIO(str(away_gk_table_tag)))[0]
            away_player_stats_dict["Keeper"] = away_gk_df
        else:
            away_player_stats_dict["Keeper"] = None  # type: ignore

        # Shots tables
        # Do these separately too because some matches only have data for 1 team
        shots_dict = {"Both": None, "Home": None, "Away": None}
        all_shots_table_tag = soup.find("table", {"id": "shots_all"})
        if all_shots_table_tag:
            all_shots_df = pd.read_html(StringIO(str(all_shots_table_tag)))[0]
            shots_dict["Both"] = all_shots_df  # type: ignore
        
        home_shots_table_tag = soup.find("table", {"id": f"shots_{home_id}"})
        if home_shots_table_tag:
            home_shots_df = pd.read_html(StringIO(str(home_shots_table_tag)))[0]
            shots_dict["Home"] = home_shots_df  # type: ignore
        
        away_shots_table_tag = soup.find("table", {"id": f"shots_{away_id}"})
        if away_shots_table_tag:
            away_shots_df = pd.read_html(StringIO(str(away_shots_table_tag)))[0]
            shots_dict["Away"] = away_shots_df  # type: ignore

        # 1-row df for output
        match_df_data = {
            "Link": link,
            "Date": date,
            "Stage": stage,
            "Home Team": home_name,
            "Away Team": away_name,
            "Home Team ID": home_id,
            "Away Team ID": away_id,
            "Home Goals": home_goals,
            "Away Goals": away_goals,
            "Home Player Stats": pd.Series(home_player_stats_dict),
            "Away Player Stats": pd.Series(away_player_stats_dict),
            "Shots": pd.Series(shots_dict)
        }
        match_df = pd.Series(match_df_data).to_frame().T

        return match_df

    # ==============================================================================================
    def scrape_matches(self, year: str, league: str) -> pd.DataFrame:
        """ Scrapes the FBref standard stats page of the chosen league season.

        Works by gathering all of the match URL's from the homepage of the chosen league season on
        FBref and then calling scrape_match() on each one.

        Parameters
        ----------
        year : str
            See the :ref:`fbref_year` `year` parameter docs for details.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        Returns
        -------
        : DataFrame
            Each row is the data from a single match.
        """
        matches_df = pd.DataFrame()
        match_links = self.get_match_links(year, league)
        for link in tqdm(match_links, desc=f'{year} {league} matches'):
            match_df = self.scrape_match(link)
            matches_df = pd.concat([matches_df, match_df], axis=0, ignore_index=True)

        # If matches were added, sort matches by date
        if matches_df.shape[0] > 0:
            matches_df = matches_df.sort_values(by='Date').reset_index(drop=True)

        return matches_df

    # ==============================================================================================
    def scrape_stats(
            self, year: str, league: str, stat_category: str
    ) -> Sequence[Union[pd.DataFrame, None]]:
        """ Scrapes a single stats category

        Adds team and player ID columns to the stats tables

        Parameters
        ----------
        year : str
            See the :ref:`fbref_year` `year` parameter docs for details.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        stat_cateogry : str
            The stat category to scrape.
        Returns
        -------
        : tuple of DataFrames or None
            (squad_stats, opponent_stats, player_stats). Tuple elements will be None if the squad
            stats category does not exist for the given `year` and `league`.
        """

        # Verify valid stat category
        if stat_category not in stats_categories.keys():
            raise ValueError(
                f'"{stat_category}" is not a valid FBref stats category. '
                f'Must be one of {list(stats_categories.keys())}.'
            )

        season_url = self.get_season_link(year, league)

        if league == 'Big 5 combined':
            # Big 5 combined has separate pages for squad and player stats
            # Make the URLs to these pages
            first_half = '/'.join(season_url.split('/')[:-1])
            second_half = season_url.split('/')[-1]
            stats_category_url_filler = stats_categories[stat_category]['url']
            players_stats_url = '/'.join([
                first_half, stats_category_url_filler, 'players',second_half
            ])
            squads_stats_url = '/'.join([
                first_half, stats_category_url_filler, 'squads', second_half
            ])

            # Get the soups from the 2 pages
            players_soup = BeautifulSoup(self._get(players_stats_url).content, 'html.parser')
            squads_soup = BeautifulSoup(self._get(squads_stats_url).content, 'html.parser')

            # Gather stats table tags
            squad_stats_tag = squads_soup.find('table', {'id': re.compile('for')})
            opponent_stats_tag = squads_soup.find('table', {'id': re.compile('against')})
            player_stats_tag = players_soup.find(
                'table',
                {'id': re.compile(f'stats_{stats_categories[stat_category]["html"]}')}
            )

            # Gather squad and opponent squad IDs
            # These are 'td' elements for Big 5
            squad_ids = [
                tag.find('a')['href'].split('/')[3] for tag
                in squad_stats_tag.find_all('td', {'data-stat': 'team'})  # type: ignore
                if tag and tag.find('a')
            ]
            opponent_ids = [
                tag.find('a')['href'].split('/')[3] for tag
                in opponent_stats_tag.find_all('td', {'data-stat': 'team'})  # type: ignore
                if tag and tag.find('a')
            ]

        else:
            # Get URL to stat category
            old_suffix = season_url.split('/')[-1]  # suffix is last element 202X-202X-divider-stats
            new_suffix = f'{stats_categories[stat_category]["url"]}/{old_suffix}'
            new_url = season_url.replace(old_suffix, new_suffix)

            self._driver_init()
            try:
                self._driver_get(new_url)
                # Wait until player stats table is loaded
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((
                    By.XPATH,
                    f'//table[contains(@id, "stats_{stats_categories[stat_category]["html"]}")]'
                )))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            finally:
                self._driver_close()

            # Gather stats table tags
            squad_stats_tag = soup.find('table', {'id': re.compile('for')})
            opponent_stats_tag = soup.find('table', {'id': re.compile('against')})
            player_stats_tag = soup.find(
                'table', {'id': re.compile(f'stats_{stats_categories[stat_category]["html"]}')}
            )

            # Gather squad and opponent squad IDs
            # These are 'th' elements for all other leagues
            squad_ids = [
                tag.find('a')['href'].split('/')[3] for tag
                in squad_stats_tag.find_all('th', {'data-stat': 'team'})[1:]  # type: ignore
                if tag and tag.find('a')
            ]
            opponent_ids = [
                tag.find('a')['href'].split('/')[3] for tag
                in opponent_stats_tag.find_all('th', {'data-stat': 'team'})[1:]  # type: ignore
                if tag and tag.find('a')
            ]

        # Get stats dataframes
        squad_stats = (pd.read_html(StringIO(str(squad_stats_tag)))[0]
                       if squad_stats_tag is not None else None)
        opponent_stats = (pd.read_html(StringIO(str(opponent_stats_tag)))[0]
                          if opponent_stats_tag is not None else None)
        player_stats = (pd.read_html(StringIO(str(player_stats_tag)))[0]
                        if player_stats_tag is not None else None)

        # Drop rows that contain duplicated table headers, add team/player IDs
        if squad_stats is not None:
            squad_drop_mask = (
                ~squad_stats.loc[:, (slice(None), 'Squad')].isna()  # type: ignore
                & (squad_stats.loc[:, (slice(None), 'Squad')] != 'Squad')  # type: ignore
            )
            squad_stats = squad_stats[squad_drop_mask.values].reset_index(drop=True)
            squad_stats['Team ID'] = squad_ids

        if opponent_stats is not None:
            opponent_drop_mask = (
                ~opponent_stats.loc[:, (slice(None), 'Squad')].isna()  # type: ignore
                & (opponent_stats.loc[:, (slice(None), 'Squad')] != 'Squad')  # type: ignore
            )
            opponent_stats = opponent_stats[opponent_drop_mask.values].reset_index(drop=True)
            opponent_stats['Team ID'] = opponent_ids

        if player_stats is not None:
            keep_players_mask = (player_stats.loc[:, (slice(None), 'Rk')] != 'Rk').values  # type: ignore
            player_stats = player_stats.loc[keep_players_mask, :].reset_index(drop=True)

        # Add player links and ID's
        if player_stats is not None:
            player_links = ['https://fbref.com' + tag.find('a')['href'] for tag
                            in player_stats_tag.find_all('td', {'data-stat': 'player'})  # type: ignore
                            if tag and tag.find('a')]
            player_stats['Player Link'] = player_links
            player_stats['Player ID'] = [x.split('/')[-2] for x in player_links]

        return squad_stats, opponent_stats, player_stats

    # ==============================================================================================
    def scrape_all_stats(self, year: str, league: str) -> dict:
        """ Scrapes all stat categories

        Runs scrape_stats() for each stats category on dumps the returned tuple
        of dataframes into a dict.

        Parameters
        ----------
        year : str
            See the :ref:`fbref_year` `year` parameter docs for details.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBref
            module file and look at the keys.
        
        Returns
        -------
        : dict
            {stat category: tuple of DataFrame, ...}, Tuple is (squad_stats, opponent_stats,
            player_stats)
        """
        return_package = dict()
        for stat_category in tqdm(stats_categories, desc=f'{year} {league} stats'):
            stats = self.scrape_stats(year, league, stat_category)
            return_package[stat_category] = stats

        return return_package

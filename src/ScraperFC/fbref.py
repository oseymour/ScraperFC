from bs4 import BeautifulSoup
import requests
from cloudscraper import CloudScraper
import time
import pandas as pd
from io import StringIO
import re
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from typing import Sequence, Union
import warnings

from .scraperfc_exceptions import InvalidYearException, InvalidLeagueException, \
    NoMatchLinksException, FBrefRateLimitException
from .utils import get_module_comps

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

comps = get_module_comps("FBREF")


class FBref():

    # ==============================================================================================
    def __init__(self, wait_time: int=7) -> None:
        # FBref rate limits bots -- https://www.sports-reference.com/bot-traffic.html
        self.wait_time = wait_time
        self.scraper = CloudScraper()

    # ==============================================================================================
    def _driver_init(self) -> None:
        """ Private, creates a headless selenium webdriver
        """
        options = Options()
        options.add_argument('--incognito')
        options.add_argument('--headless')
        options.add_argument("--log-level=2")
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
        """ Private, uses cloudscraper to get response and enforces FBref's wait time.
        """
        response = self.scraper.get(url)
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

        :param str league: .. include:: ./arg_docstrings/league.rst
        
        :return: dict(year: url, ...), URLs need to be appended to "https://fbref.com" to be a 
            complete URL.
        :rtype: dict
        """
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'FBref', list(comps.keys()))

        url = comps[league]["FBREF"]['history url']  # type: ignore
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

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: URL to the FBref page of the chosen league season
        :rtype: str
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

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: FBref links to all matches for the chosen league season
        :rtype: List[str]
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
            if (a is not None and 'match' in a['href']
                    and any([f in a['href'] for f in comps[league]["FBREF"]['finders']])
                ):
                match_urls.append('https://fbref.com' + a['href'])
        match_urls = list(set(match_urls))
        return match_urls

    # ==============================================================================================
    def scrape_league_table(self, year: str, league: str) -> Sequence[pd.DataFrame]:
        """ Scrapes the league table of the chosen league season

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        
        :returns: Returns a list of all position tables from the league's homepage on
            FBref. The first table will be the league table, all tables after that
            vary by competition.
        :rtype: List[pandas.DataFrame]
        """
        season_link = self.get_season_link(year, league)

        # Fetch HTML via CloudScraper to avoid FBref 403s that occur when pandas fetches the URL directly
        response = self._get(season_link)

        tables: Sequence[pd.DataFrame] = list()
        try:
            html = response.text
            for df in pd.read_html(html):
                if 'Rk' in df.columns:
                    # Remove all-NaN rows
                    df = df.dropna(axis=0, how='all').reset_index(drop=True)
                    # Add the df to tables
                    tables.append(df)
        except ValueError:
            # No tables found in the rendered HTML
            pass

        return tables

    # ==============================================================================================
    def scrape_match(self, link: str) -> pd.DataFrame:
        """ Scrapes an FBref match page.

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: DataFrame containing most parts of the match page if they're available (e.g. 
            formations, lineups, scores, player stats, etc.). The fields that are available vary 
            by competition and year.
        :rtype: pandas.DataFrame
        """
        if not isinstance(link, str):
            raise TypeError('`link` must be a string.')

        r = self._get(link)
        soup = BeautifulSoup(r.content, 'html.parser')

        # General match info
        scorebox_meta_tag = soup.find("div", {"class": "scorebox_meta"})
        if scorebox_meta_tag is not None:
            date = scorebox_meta_tag.find("strong").text  # type: ignore
        else:
            date = soup.find("span", {"class": "venuetime"})["data-venue-date"]  # type: ignore

        stage = soup.find("div", {"role": "main"}).find("div").text  # type: ignore

        # Team names, IDs, goals, and xG
        team_els = soup.find("div", {"class": "scorebox"}).find_all("div", recursive=False)  # type: ignore
        home_el, away_el = team_els[0], team_els[1]

        home_name = home_el.find("div").text.strip()
        home_id = home_el.find("div").find("strong").find("a")["href"].split("/")[3]
        home_goals = home_el.find("div", {"class": "score"}).text # don't cast to int because games that were awarded to one team have `*` by that team's goals

        away_name = away_el.find("div").text.strip()
        away_id = away_el.find("div").find("strong").find("a")["href"].split("/")[3]
        away_goals = away_el.find("div", {"class": "score"}).text

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

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: Each row is the data from a single match.
        :rtype: pandas.DataFrame
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

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst
        :param str stat_category: The stat category to scrape.

        :returns: (squad_stats, opponent_stats, player_stats). Tuple elements will be None if the 
            squad stats category does not contain data for the given `year` and `league`.
        :rtype: Tuple[pandas.DataFrame | None]
        """

        # Verify valid stat category
        if stat_category not in stats_categories.keys():
            raise ValueError(
                f'"{stat_category}" is not a valid FBref stats category. '
                f'Must be one of {list(stats_categories.keys())}.'
            )

        season_url = self.get_season_link(year, league)

        if 'big 5 combined' in league.lower():
            squad_id_finder = "td"  # for squad and opponent squad IDs
            squad_id_start_idx = 0  # to index the squad id elements list, to match shape of df
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

        else:  # not big 5 leagues
            squad_id_finder = "th"
            squad_id_start_idx = 1
            # Get URL to stat category
            old_suffix = season_url.split('/')[-1]  # suffix is last element 202X-202X-divider-stats
            new_suffix = f'{stats_categories[stat_category]["url"]}/{old_suffix}'
            new_url = season_url.replace(old_suffix, new_suffix)

            self._driver_init()
            try:
                # Wait for the player stats table to load
                self._driver_get(new_url)
                WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((
                    By.XPATH,
                    f'//table[contains(@id, "stats_{stats_categories[stat_category]["html"]}")]'
                )))
            except TimeoutException:
                # Don't raise this exception, the table tags won't be found. They'll be None and
                # appropriately handled later in this function.
                warnings.warn(
                    f"No player stats table ever loaded for {year} {league} {stat_category}"
                    f" ({new_url}). It is likely that there is no data for this year-league."
                )
            finally:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                self._driver_close()

                # Gather stats table tags
                squad_stats_tag = soup.find('table', {'id': re.compile('for')})
                opponent_stats_tag = soup.find('table', {'id': re.compile('against')})
                player_stats_tag = soup.find(
                    'table', {'id': re.compile(f'stats_{stats_categories[stat_category]["html"]}')}
                )

        # DO THESE THINGS WHETHER BIG 5 OR NOT
        # Get stats dataframes
        squad_stats = (
            None if squad_stats_tag is None
            else pd.read_html(StringIO(str(squad_stats_tag)))[0]
        )
        opponent_stats = (
            None if opponent_stats_tag is None
            else pd.read_html(StringIO(str(opponent_stats_tag)))[0]
        )
        player_stats = (
            None if player_stats_tag is None
            else pd.read_html(StringIO(str(player_stats_tag)))[0]
        )

        # Drop rows that contain duplicated table headers, add team/player IDs
        if squad_stats is not None:
            squad_drop_mask = (
                ~squad_stats.loc[:, (slice(None), 'Squad')].isna()  # type: ignore
                & (squad_stats.loc[:, (slice(None), 'Squad')] != 'Squad')  # type: ignore
            )
            squad_stats = squad_stats[squad_drop_mask.values].reset_index(drop=True)

            # Squad IDs
            squad_ids = [
                tag.find('a')['href'].split('/')[3]
                for tag in squad_stats_tag.find_all(squad_id_finder, {'data-stat': 'team'})[squad_id_start_idx:]  # type: ignore
                if tag and tag.find('a')
            ]
            squad_stats['Team ID'] = squad_ids

        if opponent_stats is not None:
            opponent_drop_mask = (
                ~opponent_stats.loc[:, (slice(None), 'Squad')].isna()  # type: ignore
                & (opponent_stats.loc[:, (slice(None), 'Squad')] != 'Squad')  # type: ignore
            )
            opponent_stats = opponent_stats[opponent_drop_mask.values].reset_index(drop=True)

            # Opponent squad IDs
            opponent_ids = [
                tag.find('a')['href'].split('/')[3]
                for tag in opponent_stats_tag.find_all(squad_id_finder, {'data-stat': 'team'})[squad_id_start_idx:]  # type: ignore
                if tag and tag.find('a')
            ]
            opponent_stats['Team ID'] = opponent_ids

        if player_stats is not None:
            keep_players_mask = (player_stats.loc[:, (slice(None), 'Rk')] != 'Rk').values  # type: ignore
            player_stats = player_stats.loc[keep_players_mask, :].reset_index(drop=True)

            # Add player links and ID's
            player_links = [
                'https://fbref.com' + tag.find('a')['href']
                for tag in player_stats_tag.find_all('td', {'data-stat': 'player'})  # type: ignore
                if tag and tag.find('a')
            ]
            player_stats['Player Link'] = player_links
            player_stats['Player ID'] = [x.split('/')[-2] for x in player_links]

        return squad_stats, opponent_stats, player_stats

    # ==============================================================================================
    def scrape_all_stats(self, year: str, league: str) -> dict:
        """ Scrapes all stat categories

        Runs scrape_stats() for each stats category on dumps the returned tuple
        of dataframes into a dict.

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: {stat category: tuple of DataFrame, ...}, Tuple is (squad_stats, opponent_stats,
            player_stats)
        :rtype: dict
        """
        return_package = dict()
        for stat_category in tqdm(stats_categories, desc=f'{year} {league} stats'):
            stats = self.scrape_stats(year, league, stat_category)
            return_package[stat_category] = stats

        return return_package

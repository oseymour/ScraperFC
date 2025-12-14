import re
import time
from io import StringIO
from typing import Sequence
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from botasaurus.browser import browser, ElementWithSelectorNotFoundException

from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException,\
    NoMatchLinksException
from .utils import get_module_comps
from .fbref_helpers import _get_date, _get_stage, _get_team_names, _get_team_ids, _get_goals,\
    _get_player_stats, _get_shots
from .fbref_match import FBrefMatch

stats_categories = {
    "standard": {"url": "stats", "html": "standard"},
    "goalkeeping": {"url": "keepers", "html": "keeper"},
    "advanced goalkeeping": {"url": "keepersadv", "html": "keeper_adv"},
    "shooting": {"url": "shooting", "html": "shooting"},
    "passing": {"url": "passing", "html": "passing"},
    "pass types": {"url": "passing_types", "html": "passing_types"},
    "goal and shot creation": {"url": "gca", "html": "gca"},
    "defensive": {"url": "defense", "html": "defense"},
    "possession": {"url": "possession", "html": "possession"},
    "playing time": {"url": "playingtime", "html": "playing_time"},
    "misc": {"url": "misc", "html": "misc"},
}

comps = get_module_comps("FBREF")


class FBref:
    # ==============================================================================================
    def __init__(self, wait_time: int = 6) -> None:
        # FBref rate limits bots -- https://www.sports-reference.com/bot-traffic.html
        self.wait_time = wait_time

    # ==============================================================================================
    def _get_soup(self, url: str) -> BeautifulSoup:
        """ Private, gets soup using botasaurus. """
        @browser(
            headless=False, block_images_and_css=False,
            wait_for_complete_page_load=False,
            output=None, create_error_logs=False,
        )
        def _(driver, url):  # type: ignore
            driver.google_get(url)
            while True:
                try:
                    driver.wait_for_element("body.fb", wait=10)
                    break
                except ElementWithSelectorNotFoundException:
                    driver.reload()
            return BeautifulSoup(driver.page_html, "html.parser")
        return _(url)

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """Finds all of the valid years and their URLs for a given competition

        :param str league: .. include:: ./arg_docstrings/league.rst

        :return: dict(year: url, ...), URLs need to be appended to "https://fbref.com" to be a
            complete URL.
        :rtype: dict
        """
        if not isinstance(league, str):
            raise TypeError("`league` must be a string.")
        if league not in comps.keys():
            raise InvalidLeagueException(league, "FBref", list(comps.keys()))

        url = comps[league]["FBREF"]["history url"]  # type: ignore

        soup = self._get_soup(url)

        valid_seasons = {
            x.text: "https://fbref.com" + x.find("a")["href"]
            for x in soup.find_all("th", {"data-stat": re.compile("year"), "scope": "row"})
            if x.find("a")
        }

        return valid_seasons

    # ==============================================================================================
    def get_match_links(self, year: str, league: str) -> Sequence[str]:
        """Gets all match links for the chosen league season.

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: FBref links to all matches for the chosen league season
        :rtype: List[str]
        """
        valid_seasons = self.get_valid_seasons(league)
        if not isinstance(year, str):
            raise TypeError("`year` must be a string.")
        if year not in valid_seasons:
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        # Get the URL for the fixtures page
        season_url = valid_seasons[year]
        fixtures_url = season_url.split("/")
        fixtures_url.insert(-1, "schedule")
        fixtures_url = "/".join(fixtures_url).replace("Stats", "Scores-and-Fixtures")

        soup = self._get_soup(fixtures_url)

        match_els = [
            td for td in
            soup.find_all("td", {"data-stat": "score"})
            if td.get("class") == ["center"]
        ]

        match_urls = ["https://fbref.com" + el.find("a").get("href") for el in match_els]

        match_urls = list(set(match_urls))  # remove duplicate links

        if len(match_urls) == 0:
            raise NoMatchLinksException(year, league, fixtures_url)

        return match_urls

    # ==============================================================================================
    def scrape_league_table(self, year: str, league: str) -> Sequence[pd.DataFrame]:
        """Scrapes the league table of the chosen league season

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: Returns a list of all position tables from the league's homepage on
            FBref. The first table will be the league table, all tables after that
            vary by competition.
        :rtype: List[pandas.DataFrame]
        """
        if not isinstance(year, str):
            raise TypeError("`year` must be a string.")
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons:
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        url = valid_seasons[year]

        soup = self._get_soup(url)

        tables = list()
        for df in pd.read_html(StringIO(str(soup))):
            if ("Rk" in df.columns) and ("Squad" in df.columns):
                # Remove all-NaN rows
                df = df.dropna(axis=0, how="all").reset_index(drop=True)

                # Add the df to tables
                tables.append(df)
        return tables

    # ==============================================================================================
    def scrape_match(self, link: str) -> FBrefMatch:
        """Scrapes an FBref match page.

        :param year: .. include:: ./arg_docstrings/year_fbref.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str

        :returns: Match data
        :rtype: FBrefMatch
        """
        if not isinstance(link, str):
            raise TypeError("`link` must be a string.")
        soup = self._get_soup(link)

        date = _get_date(soup)
        stage = _get_stage(soup)
        home_name, away_name = _get_team_names(soup)
        home_id, away_id = _get_team_ids(soup)
        home_goals, away_goals = _get_goals(soup)
        player_stats = _get_player_stats(soup)
        shots = _get_shots(soup)

        return FBrefMatch(
            url=link,
            date=date,
            stage=stage,
            home_team=home_name,
            away_team=away_name,
            home_id=home_id,
            away_id=away_id,
            home_goals=home_goals,
            away_goals=away_goals,
            home_player_stats=player_stats["home"],
            away_player_stats=player_stats["away"],
            all_shots=shots["all"],
            home_shots=shots["home"],
            away_shots=shots["away"],
        )

    # ==============================================================================================
    def scrape_matches(self, year: str, league: str) -> list[FBrefMatch]:
        """Scrapes the FBref standard stats page of the chosen league season.

        Works by gathering all of the match URL's from the homepage of the chosen league season on
        FBref and then calling scrape_match() on each one.

        :param year: .. include:: ./arg_docstrings/year_fbref.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str

        :returns: List of match datas
        :rtype: list[FBrefMatch]
        """
        matches = list()
        match_links = self.get_match_links(year, league)
        for link in tqdm(match_links, desc=f"{year} {league} matches"):
            start_time = time.time()
            match = self.scrape_match(link)
            elapsed = time.time() - start_time
            if elapsed < self.wait_time:
                time.sleep(self.wait_time - elapsed)
            matches.append(match)

        return matches

    # ==============================================================================================
    def scrape_stats(
        self, year: str, league: str, stat_category: str
    ) -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
        """Scrapes a single stats category

        Adds team and player ID columns to the stats tables

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst
        :param str stat_category: The stat category to scrape.

        :returns: (squad_stats, opponent_stats, player_stats). Tuple elements will be None if the
            squad stats category does not contain data for the given `year` and `league`.
        :rtype: tuple[pd.DataFrame | None]
        """
        valid_seasons = self.get_valid_seasons(league)
        if not isinstance(year, str):
            raise TypeError("`year` must be a string.")
        if year not in valid_seasons:
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        # Verify valid stat category
        if stat_category not in stats_categories.keys():
            raise ValueError(
                f'"{stat_category}" is not a valid FBref stats category. '
                f"Must be one of {list(stats_categories.keys())}."
            )

        season_url = valid_seasons[year]

        if "big 5 combined" in league.lower():
            squad_id_finder = "td"  # for squad and opponent squad IDs
            squad_id_start_idx = 0  # to index the squad id elements list, to match shape of df
            # Big 5 combined has separate pages for squad and player stats
            # Make the URLs to these pages
            first_half = "/".join(season_url.split("/")[:-1])
            second_half = season_url.split("/")[-1]
            stats_category_url_filler = stats_categories[stat_category]["url"]
            players_stats_url = "/".join(
                [first_half, stats_category_url_filler, "players", second_half]
            )
            squads_stats_url = "/".join(
                [first_half, stats_category_url_filler, "squads", second_half]
            )

            # Get the soups from the 2 pages
            # players_soup = BeautifulSoup(self._get(players_stats_url).content, "html.parser")
            # squads_soup = BeautifulSoup(self._get(squads_stats_url).content, "html.parser")
            players_soup = self._get_soup(players_stats_url)
            squads_soup = self._get_soup(squads_stats_url)

            # Gather stats table tags
            squad_stats_tag = squads_soup.find("table", {"id": re.compile("for")})
            opponent_stats_tag = squads_soup.find("table", {"id": re.compile("against")})
            player_stats_tag = players_soup.find(
                "table", {"id": re.compile(f'stats_{stats_categories[stat_category]["html"]}')}
            )

        else:  # not big 5 leagues
            squad_id_finder = "th"
            squad_id_start_idx = 1
            # Get URL to stat category
            old_suffix = season_url.split("/")[-1]  # suffix is last element 202X-202X-divider-stats
            new_suffix = f'{stats_categories[stat_category]["url"]}/{old_suffix}'
            new_url = season_url.replace(old_suffix, new_suffix)

            soup = self._get_soup(new_url)

            # Gather stats table tags
            squad_stats_tag = soup.find("table", {"id": re.compile("for")})
            opponent_stats_tag = soup.find("table", {"id": re.compile("against")})
            player_stats_tag = soup.find(
                "table", {"id": re.compile(f'stats_{stats_categories[stat_category]["html"]}')}
            )

        # DO THESE THINGS WHETHER BIG 5 OR NOT
        # Get stats dataframes
        squad_stats = (
            None if squad_stats_tag is None else pd.read_html(StringIO(str(squad_stats_tag)))[0]
        )
        opponent_stats = (
            None
            if opponent_stats_tag is None
            else pd.read_html(StringIO(str(opponent_stats_tag)))[0]
        )
        player_stats = (
            None if player_stats_tag is None else pd.read_html(StringIO(str(player_stats_tag)))[0]
        )

        # Drop rows that contain duplicated table headers, add team/player IDs
        if squad_stats is not None:
            squad_drop_mask = (
                ~squad_stats.loc[:, (slice(None), "Squad")].isna()  # type: ignore
                & (squad_stats.loc[:, (slice(None), "Squad")] != "Squad")  # type: ignore
            )
            squad_stats = squad_stats[squad_drop_mask.values].reset_index(drop=True)

            # Squad IDs
            squad_ids = [
                tag.find("a")["href"].split("/")[3]
                for tag in squad_stats_tag.find_all(squad_id_finder, {"data-stat": "team"})[  # type: ignore
                    squad_id_start_idx:
                ]
                if tag and tag.find("a")
            ]
            squad_stats["Team ID"] = squad_ids

        if opponent_stats is not None:
            opponent_drop_mask = (
                ~opponent_stats.loc[:, (slice(None), "Squad")].isna()  # type: ignore
                & (opponent_stats.loc[:, (slice(None), "Squad")] != "Squad")  # type: ignore
            )
            opponent_stats = opponent_stats[opponent_drop_mask.values].reset_index(drop=True)

            # Opponent squad IDs
            opponent_ids = [
                tag.find("a")["href"].split("/")[3]
                for tag in opponent_stats_tag.find_all(squad_id_finder, {"data-stat": "team"})[  # type: ignore
                    squad_id_start_idx:
                ]
                if tag and tag.find("a")
            ]
            opponent_stats["Team ID"] = opponent_ids

        if player_stats is not None:
            keep_players_mask = (player_stats.loc[:, (slice(None), "Rk")] != "Rk").values  # type: ignore
            player_stats = player_stats.loc[keep_players_mask, :].reset_index(drop=True)

            # Add player links and ID's
            player_links = [
                "https://fbref.com" + tag.find("a")["href"]
                for tag in player_stats_tag.find_all("td", {"data-stat": "player"})  # type: ignore
                if tag and tag.find("a")
            ]
            player_stats["Player Link"] = player_links
            player_stats["Player ID"] = [x.split("/")[-2] for x in player_links]

        return squad_stats, opponent_stats, player_stats

    # ==============================================================================================
    def scrape_all_stats(self, year: str, league: str) -> dict:
        """Scrapes all stat categories

        Runs scrape_stats() for each stats category on dumps the returned tuple
        of dataframes into a dict.

        :param str year: .. include:: ./arg_docstrings/year_fbref.rst
        :param str league: .. include:: ./arg_docstrings/league.rst

        :returns: {stat category: tuple of DataFrame, ...}, Tuple is (squad_stats, opponent_stats,
            player_stats)
        :rtype: dict
        """
        return_package = dict()
        for stat_category in tqdm(stats_categories, desc=f"{year} {league} stats"):
            start_time = time.time()
            stats = self.scrape_stats(year, league, stat_category)
            elapsed = time.time() - start_time
            if elapsed < self.wait_time:
                time.sleep(self.wait_time - elapsed)
            return_package[stat_category] = stats

        return return_package

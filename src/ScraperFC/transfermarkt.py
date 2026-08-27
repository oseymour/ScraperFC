from tqdm import tqdm
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cloudscraper
import warnings
from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from ScraperFC.utils import get_module_comps, botasaurus_request_get_soup

TRANSFERMARKT_ROOT = "https://www.transfermarkt.us"

comps = get_module_comps("TRANSFERMARKT")


def parse_height(height_str: str):
    """ Parse a Transfermarkt height string into metres

    Transfermarkt serves metric ("1,91 m") or imperial ("6 ft 6 in") heights,
    depending on the domain and locale of the request.

    :param height_str: Height string from a player page
    :type height_str: str
    :return: Height in metres, or None if the page doesn't have one
    :rtype: float or None
    """
    height_str = height_str.strip()

    imperial_match = re.match(
        r"^(\d+)\s*ft(?:\s*(\d+)\s*in)?$", height_str, flags=re.IGNORECASE
    )
    if imperial_match is not None:
        feet = int(imperial_match.group(1))
        inches = int(imperial_match.group(2) or 0)
        return round((feet * 12 + inches) * 0.0254, 2)

    metric_match = re.match(r"^(\d+)[,.](\d+)\s*m$", height_str, flags=re.IGNORECASE)
    if metric_match is not None:
        return float(f"{metric_match.group(1)}.{metric_match.group(2)}")

    return None


def scrape_market_value_history(player_id: str):
    """ Scrape a player's market value history

    Transfermarkt serves the market value chart from a JSON endpoint, not from the player page
    HTML.

    :param player_id: Transfermarkt player ID, the last part of a player URL
    :type player_id: str
    :return: Dataframe of the player's market value history, or None if the player doesn't have
        one
    :rtype: pd.DataFrame or None
    """
    r = requests.get(
        f"{TRANSFERMARKT_ROOT}/ceapi/marketValueDevelopment/graph/{player_id}",
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +\
                "(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }
    )
    if r.status_code != 200:
        return None
    try:
        entries = r.json()["list"]
    except (ValueError, KeyError, TypeError):
        return None
    if len(entries) == 0:
        return None
    return pd.DataFrame({
        "date": [entry["datum_mw"] for entry in entries],
        "value": [int(entry["y"]) for entry in entries]
    })


def scrape_transfer_history(player_id: str):
    """ Scrape a player's transfer history

    Transfermarkt serves the transfer history table from a JSON endpoint, not from the player page
    HTML.

    :param player_id: Transfermarkt player ID, the last part of a player URL
    :type player_id: str
    :return: Dataframe of the player's transfer history, or None if the player doesn't have one
    :rtype: pd.DataFrame or None
    """
    r = requests.get(
        f"{TRANSFERMARKT_ROOT}/ceapi/transferHistory/list/{player_id}",
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +\
                "(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }
    )
    if r.status_code != 200:
        return None
    try:
        transfers = r.json()["transfers"]
    except (ValueError, KeyError, TypeError):
        return None
    if len(transfers) == 0:
        return None
    return pd.DataFrame({
        "Season": [t.get("season") for t in transfers],
        "Date": [t.get("date") for t in transfers],
        "Left": [t.get("from", {}).get("clubName") for t in transfers],
        "Joined": [t.get("to", {}).get("clubName") for t in transfers],
        "MV": [t.get("marketValue") for t in transfers],
        "Fee": [t.get("fee") for t in transfers]
    })


class Transfermarkt():

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """ Return valid seasons for the chosen league

        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If ``league`` is not a string
        :raises InvalidLeagueException: If ``league`` is not a valid league for this module.
        :return: year str is key, ID is value
        :rtype: dict
        """
        if not isinstance(league, str):
            raise TypeError("`league` must be a string.")
        if league not in comps.keys():
            raise InvalidLeagueException(league, "Transfermarkt", list(comps.keys()))

        season_select_tag = None
        while not season_select_tag:
            soup = botasaurus_request_get_soup(comps[league]["TRANSFERMARKT"])
            season_select_tag = soup.find("select", {"name": "saison_id"})
        season_tags = season_select_tag.find_all("option")  # type: ignore
        valid_seasons = {x.text: x["value"] for x in season_tags}
        return valid_seasons

    # ==============================================================================================
    def get_club_links(self, year: str, league: str) -> list[str]:
        """ Gathers all Transfermarkt club URL"s for the chosen league season.

        :param year: .. include:: ./arg_docstrings/year_transfermarkt.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :raises TypeError: If any parameters are the wrong type
        :raises InvalidYearException: If ``year`` is not a valid year for the league.
        :return: List of club URLs
        :rtype: list[str]
        """
        if not isinstance(year, str):
            raise TypeError("`year` must be a string.")
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))

        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(
                scraper.get(f"{comps[league]['TRANSFERMARKT']}/plus/?saison_id={valid_seasons[year]}").content,
                "html.parser"
            )
            items_table_tag = soup.find("table", {"class": "items"})
            if items_table_tag is None:
                warnings.warn(
                    f"No club links table found for {year} {league}. Returning empty list."
                )
                club_links = list()
            else:
                club_els = items_table_tag.find_all("td", {"class": "hauptlink no-border-links"})  # type: ignore
                club_links = [TRANSFERMARKT_ROOT + x.find("a")["href"] for x in club_els]
            return club_links
        finally:
            scraper.close()

    # ==============================================================================================
    def get_player_links(self, year: str, league: str) -> list[str]:
        """ Gathers all Transfermarkt player URL"s for the chosen league season.

        :param year: .. include:: ./arg_docstrings/year_transfermarkt.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: List of player URLs
        :rtype: list[str]
        """
        player_links = list()
        scraper = cloudscraper.CloudScraper()
        try:
            club_links = self.get_club_links(year, league)
            for club_link in tqdm(club_links, desc=f"{year} {league} player links"):
                soup = BeautifulSoup(scraper.get(club_link).content, "html.parser")
                player_table = soup.find("table", {"class": "items"})
                if player_table is not None:
                    player_els = player_table.find_all("td", {"class": "hauptlink"})  # type: ignore
                    p_links = [
                        TRANSFERMARKT_ROOT + x.find("a")["href"] for x in player_els
                        if x.find("a") is not None
                    ]
                    player_links += p_links
            return list(set(player_links))
        finally:
            scraper.close()

    # ==============================================================================================
    def get_match_links(self, year: str, league: str) -> list[str]:
        """ Returns all match links for a given competition season.

        :param year: .. include:: ./arg_docstrings/year_transfermarkt.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: List of match URLs
        :rtype: list[str]
        """
        valid_seasons = self.get_valid_seasons(league)
        fixtures_url = f"{comps[league]['TRANSFERMARKT'].replace('startseite', 'gesamtspielplan')}/saison_id/{valid_seasons[year]}"
        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(scraper.get(fixtures_url).content, "html.parser")
            match_tags = soup.find_all("a", {"class": "ergebnis-link"})
            match_links = ["https://www.transfermarkt.us" + x["href"] for x in match_tags]
            return match_links
        finally:
            scraper.close()

    # ==============================================================================================
    def scrape_players(self, year: str, league: str) -> pd.DataFrame:
        """ Gathers all player info for the chosen league season.

        :param year: .. include:: ./arg_docstrings/year_transfermarkt.rst
        :type year: str
        :param league: .. include:: ./arg_docstrings/league.rst
        :type league: str
        :return: Each row is a player and contains some of the information from their Transfermarkt
        :rtype: pd.DataFrame
        """
        player_links = self.get_player_links(year, league)
        df = pd.DataFrame()
        for player_link in tqdm(player_links, desc=f"{year} {league} players"):
            player = self.scrape_player(player_link)
            df = pd.concat([df, player], axis=0, ignore_index=True)

        return df

    # ==============================================================================================
    def scrape_player(self, player_link: str) -> pd.DataFrame:
        """ Scrape a single player Transfermarkt link

        :param player_link: Valid player Transfermarkt URL
        :type player_link: str
        :raises ValueError: If more than 1 element exists for some HTML elements.
        :return: 1-row dataframe with all of the player details
        :rtype: pd.DataFrame
        """
        r = requests.get(
            player_link,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +\
                    "(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
            }
        )
        soup = BeautifulSoup(r.content, "html.parser")

        # Name
        name_tag = soup.find("h1", {"class": "data-header__headline-wrapper"})
        name = name_tag.text.split("\n")[-1].strip()  # type: ignore

        # Value
        try:
            value_tag = soup.find("a", {"class": "data-header__market-value-wrapper"})
            value = value_tag.text.split(" ")[0]  # type: ignore
            value_last_updated_tag = soup.find("a", {"class": "data-header__market-value-wrapper"})
            value_last_updated = value_last_updated_tag.text.split("Last update: ")[-1]  # type: ignore
        except AttributeError:
            value = None
            value_last_updated = None

        # DOB and age
        dob_el = soup.find("span", {"itemprop": "birthDate"})
        if dob_el is None:
            dob, age = None, None
        else:
            dob = " ".join(dob_el.text.strip().split(" ")[:3])
            age = int(dob_el.text.strip().split(" ")[-1].replace("(", "").replace(")", ""))

        # Height
        height_tag = soup.find("span", {"itemprop": "height"})
        if height_tag is None:
            height = None
        else:
            height = parse_height(height_tag.text)

        # Nationality and citizenships
        nationality_el = soup.find("span", {"itemprop": "nationality"})
        if nationality_el is not None:
            nationality = nationality_el.getText().replace("\n", "").strip()  # type: ignore
        else:
            nationality = None

        citizenship_els = soup.find_all(
            "span", {"class": "info-table__content info-table__content--bold"}
        )
        flag_els = [
            flag_el for el in citizenship_els
            for flag_el in el.find_all("img", {"class": "flaggenrahmen"})
        ]
        citizenship = list(set(el["title"] for el in flag_els))

        # Position
        position_el = soup.find("dd", {"class": "detail-position__position"})
        if position_el is None:
            position_el = [
                el for el in soup.find_all("li", {"class": "data-header__label"})
                if "position" in el.text.lower()
            ][0].find("span")
        position = position_el.text.strip()
        try:
            other_positions = [
                el.text for el in
                soup.find("div", {"class": "detail-position__position"}).find_all("dd")  # type: ignore
            ]
        except AttributeError:
            other_positions = None
        other_positions = None if other_positions is None else pd.DataFrame(other_positions)  # type: ignore

        # Data header fields
        team = soup.find("span", {"class": "data-header__club"})
        team = None if team is None else team.text.strip()  # type: ignore

        data_headers_labels = soup.find_all("span", {"class": "data-header__label"})
        # Last club
        last_club = [
            x.text.split(":")[-1].strip() for x in data_headers_labels
            if "last club" in x.text.lower()
        ]
        if len(last_club) >= 2:
            raise ValueError("More than one last club found")
        last_club = None if len(last_club) == 0 else last_club[0]  # type: ignore
        # "Since" date
        since_date = [
            x.text.split(":")[-1].strip() for x in data_headers_labels
            if "since" in x.text.lower()
        ]
        if len(since_date) >= 2:
            raise ValueError("More than one since date found")
        since_date = None if len(since_date) == 0 else since_date[0]  # type: ignore
        # "Joined" date
        joined_date = [
            x.text.split(":")[-1].strip() for x in data_headers_labels if "joined" in x.text.lower()
        ]
        if len(joined_date) >= 2:
            raise ValueError("More than one joined date found")
        joined_date = None if len(joined_date) == 0 else joined_date[0]  # type: ignore
        # Contract expiration date
        contract_expiration = [
            x.text.split(":")[-1].strip() for x in data_headers_labels
            if "contract expires" in x.text.lower()
        ]
        if len(contract_expiration) >= 2:
            raise ValueError("More than one contract expiration date found")
        contract_expiration = None if len(contract_expiration) == 0 else contract_expiration[0]  # type: ignore

        # Market value history
        market_value_history = scrape_market_value_history(player_link.split("/")[-1])

        # Transfer History
        transfer_history = scrape_transfer_history(player_link.split("/")[-1])

        player = pd.Series(dtype=object)
        player["Name"] = name
        player["ID"] = player_link.split("/")[-1]
        player["Value"] = value
        player["Value last updated"] = value_last_updated
        player["DOB"] = dob
        player["Age"] = age
        player["Height (m)"] = height
        player["Nationality"] = nationality
        player["Citizenship"] = citizenship
        player["Position"] = position
        player["Other positions"] = other_positions
        player["Team"] = team
        player["Last club"] = last_club
        player["Since"] = since_date
        player["Joined"] = joined_date
        player["Contract expiration"] = contract_expiration
        player["Market value history"] = market_value_history
        player["Transfer history"] = transfer_history

        return player.to_frame().T

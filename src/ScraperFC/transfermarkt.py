from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import pandas as pd
import cloudscraper
from typing import Sequence
import warnings

TRANSFERMARKT_ROOT = "https://www.transfermarkt.us"

comps = {
    "EPL": "https://www.transfermarkt.us/premier-league/startseite/wettbewerb/GB1",
    "EFL Championship": "https://www.transfermarkt.us/championship/startseite/wettbewerb/GB2",
    "EFL1": "https://www.transfermarkt.us/league-one/startseite/wettbewerb/GB3",
    "EFL2": "https://www.transfermarkt.us/league-two/startseite/wettbewerb/GB4",
    "Bundesliga": "https://www.transfermarkt.us/bundesliga/startseite/wettbewerb/L1",
    "2.Bundesliga": "https://www.transfermarkt.us/2-bundesliga/startseite/wettbewerb/L2",
    "Serie A": "https://www.transfermarkt.us/serie-a/startseite/wettbewerb/IT1",
    "Serie B": "https://www.transfermarkt.us/serie-b/startseite/wettbewerb/IT2",
    "La Liga": "https://www.transfermarkt.us/laliga/startseite/wettbewerb/ES1",
    "La Liga 2": "https://www.transfermarkt.us/laliga2/startseite/wettbewerb/ES2",
    "Ligue 1": "https://www.transfermarkt.us/ligue-1/startseite/wettbewerb/FR1",
    "Ligue 2": "https://www.transfermarkt.us/ligue-2/startseite/wettbewerb/FR2",
    "Eredivisie": "https://www.transfermarkt.us/eredivisie/startseite/wettbewerb/NL1",
    "Scottish PL": "https://www.transfermarkt.us/scottish-premiership/startseite/wettbewerb/SC1",
    "Super Lig": "https://www.transfermarkt.us/super-lig/startseite/wettbewerb/TR1",
    "Jupiler Pro League": "https://www.transfermarkt.us/jupiler-pro-league/startseite/wettbewerb/BE1",  # noqa: E501
    "Liga Nos": "https://www.transfermarkt.us/liga-nos/startseite/wettbewerb/PO1",
    "Russian Premier League": "https://www.transfermarkt.us/premier-liga/startseite/wettbewerb/RU1",
    "Brasileirao": "https://www.transfermarkt.us/campeonato-brasileiro-serie-a/startseite/wettbewerb/BRA1",  # noqa: E501
    "Argentina Liga Profesional": "https://www.transfermarkt.us/superliga/startseite/wettbewerb/AR1N",  # noqa: E501
    "MLS": "https://www.transfermarkt.us/major-league-soccer/startseite/wettbewerb/MLS1",
    "Turkish Super Lig": "https://www.transfermarkt.us/super-lig/startseite/wettbewerb/TR1",
    "Primavera 1": "https://www.transfermarkt.us/primavera-1/startseite/wettbewerb/IJ1",
    "Primavera 2 - A": "https://www.transfermarkt.us/primavera-2a/startseite/wettbewerb/IJ2A",
    "Primavera 2 - B": "https://www.transfermarkt.us/primavera-2b/startseite/wettbewerb/IJ2B",
    "Campionato U18": "https://www.transfermarkt.us/campionato-nazionale-under-18/startseite/wettbewerb/ITJ7",  # noqa: E501
}


class Transfermarkt():

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> dict:
        """ Return valid seasons for the chosen league
        
        Parameters
        ----------
        league : str
            The league to gather valid seasons for
        
        Returns
        -------
        : dict
            {year str: year id, ...}
        """
        if not isinstance(league, str): 
            raise TypeError("`league` must be a string.")
        if league not in comps.keys():
            raise InvalidLeagueException(league, "Transfermarkt", list(comps.keys()))
        
        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(scraper.get(comps[league]).content, "html.parser")
            season_tags = soup.find("select", {"name": "saison_id"}).find_all("option")  # type: ignore
            valid_seasons = dict([(x.text, x["value"]) for x in season_tags])
            return valid_seasons
        finally:
            scraper.close()
        
    # ==============================================================================================
    def get_club_links(self, year: str, league: str) -> Sequence[str]:
        """ Gathers all Transfermarkt club URL"s for the chosen league season.
        
        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : list of str
            List of the club URLs
        """
        if not isinstance(year, str):
            raise TypeError("`year` must be a string.")
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons.keys():
            raise InvalidYearException(year, league, list(valid_seasons.keys()))
        
        scraper = cloudscraper.CloudScraper()
        try:
            soup = BeautifulSoup(
                scraper.get(f"{comps[league]}/plus/?saison_id={valid_seasons[year]}").content,
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
    def get_player_links(self, year: str, league: str) -> Sequence[str]:
        """ Gathers all Transfermarkt player URL"s for the chosen league season.
        
        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : list of str
            List of the player URLs
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
    def get_match_links(self, year: str, league: str) -> Sequence[str]:
        """ Returns all match links for a given competition season.

        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : list of str
            List of the match URLs
        """
        valid_seasons = self.get_valid_seasons(league)
        fixtures_url = f"{comps[league].replace('startseite', 'gesamtspielplan')}/saison_id/{valid_seasons[year]}"
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
        
        Parameters
        ----------
        year : str
            See the :ref:`transfermarkt_year` `year` parameter docs for details.
        league : str
            League to scrape.
        
        Returns
        -------
        : DataFrame
            Each row is a player and contains some of the information from their Transfermarkt
            player profile.
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

        Parameters
        ----------
        player_link : str
            Valid player Transfermarkt URL

        Returns
        -------
        : DataFrame
            1-row dataframe with all of the player details
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
            height_str = height_tag.text.strip()
            if height_str in ["N/A", "- m"]:
                height = None
            else:
                height = float(height_str.replace(" m", "").replace(",", "."))

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
        citizenship = list(set([el["title"] for el in flag_els]))
        
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
        assert len(last_club) < 2
        last_club = None if len(last_club) == 0 else last_club[0]  # type: ignore
        # "Since" date
        since_date = [
            x.text.split(":")[-1].strip() for x in data_headers_labels
            if "since" in x.text.lower()
        ]
        assert len(since_date) < 2
        since_date = None if len(since_date) == 0 else since_date[0]  # type: ignore
        # "Joined" date
        joined_date = [
            x.text.split(":")[-1].strip() for x in data_headers_labels if "joined" in x.text.lower()
        ]
        assert len(joined_date) < 2
        joined_date = None if len(joined_date) == 0 else joined_date[0]  # type: ignore
        # Contract expiration date
        contract_expiration = [
            x.text.split(":")[-1].strip() for x in data_headers_labels
            if "contract expires" in x.text.lower()
        ]
        assert len(contract_expiration) < 2
        contract_expiration = None if len(contract_expiration) == 0 else contract_expiration[0]  # type: ignore
        
        # Market value history
        try:
            script = [
                s for s in soup.find_all("script", {"type": "text/javascript"})
                if "var chart = new Highcharts.Chart" in str(s)
            ][0]
            values = [int(s.split(",")[0]) for s in str(script).split("y\":")[2:-2]]
            dates = [
                s.split("datum_mw\":")[-1].split(",\"x")[0].replace("\\x20", " ").replace("\"", "")
                for s in str(script).split("y\":")[2:-2]
            ]
            market_value_history = pd.DataFrame({"date": dates, "value": values})
        except IndexError:
            market_value_history = None
        
        # Transfer History
        rows = soup.find_all("div", {"class": "grid tm-player-transfer-history-grid"})
        transfer_history = pd.DataFrame(
            data=[[s.strip() for s in row.getText().split("\n\n") if s != ""] for row in rows],
            columns=["Season", "Date", "Left", "Joined", "MV", "Fee", ""]
        ).drop(
            columns=[""]
        )
        
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

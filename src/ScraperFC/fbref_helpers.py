from bs4 import BeautifulSoup
from io import StringIO
import re
import pandas as pd


def _get_date(soup: BeautifulSoup) -> str:
    """ Gets match date
    """
    scorebox_meta_tag = soup.find("div", {"class": "scorebox_meta"})
    if scorebox_meta_tag is not None:
        date = scorebox_meta_tag.find("strong").text  # type: ignore
    else:
        date = soup.find("span", {"class": "venuetime"})["data-venue-date"]  # type: ignore
    return date

def _get_stage(soup: BeautifulSoup) -> str:
    """ Gets the stage description
    """
    stage = soup.find("div", {"role": "main"}).find("div").text  # type: ignore
    return stage

def _get_team_names(soup: BeautifulSoup) -> tuple[str, str]:
    """ Gets home and away team names
    """
    team_els = soup.find("div", {"class": "scorebox"}).find_all("div", recursive=False)  # type: ignore
    home_el, away_el = team_els[0], team_els[1]
    home_name = home_el.find("div").text.strip()
    away_name = away_el.find("div").text.strip()
    return home_name, away_name

def _get_team_ids(soup: BeautifulSoup) -> tuple[str, str]:
    """ Gets home and away team IDs
    """
    team_els = soup.find("div", {"class": "scorebox"}).find_all("div", recursive=False)  # type: ignore
    home_el, away_el = team_els[0], team_els[1]
    home_id = home_el.find("div").find("strong").find("a")["href"].split("/")[3]
    away_id = away_el.find("div").find("strong").find("a")["href"].split("/")[3]
    return home_id, away_id

def _get_goals(soup: BeautifulSoup) -> tuple[str, str]:
    """ Gets home and away team goals

    Don't cast to int because games that were awarded to one team have `*` by that team's goals
    """
    team_els = soup.find("div", {"class": "scorebox"}).find_all("div", recursive=False)  # type: ignore
    home_el, away_el = team_els[0], team_els[1]
    home_goals = home_el.find("div", {"class": "score"}).text
    away_goals = away_el.find("div", {"class": "score"}).text
    return home_goals, away_goals

def _get_player_stats(soup: BeautifulSoup) -> dict[str, dict[str, pd.DataFrame]]:
    """ Gets player stats for home and away teams
    """
    home_id, away_id = _get_team_ids(soup)

    home_tables = soup.find_all("table", {"id": re.compile(f"stats_{home_id}")})
    home_player_stats = dict()
    for table in home_tables:
        key = table["id"].replace(f"stats_{home_id}", "").strip("_")
        df = pd.read_html(StringIO(str(table)))[0]
        home_player_stats[key] = df

    away_tables = soup.find_all("table", {"id": re.compile(f"stats_{away_id}")})
    away_player_stats = dict()
    for table in away_tables:
        key = table["id"].replace(f"stats_{away_id}", "").strip("_")
        df = pd.read_html(StringIO(str(table)))[0]
        away_player_stats[key] = df

    return {"home": home_player_stats, "away": away_player_stats}

def _get_shots(soup: BeautifulSoup) -> dict[str, pd.DataFrame]:
    """ Gets shot data
    """
    home_id, away_id = _get_team_ids(soup)
    all_el = soup.find("table", {"id": "shots_all"})
    all_shots = pd.read_html(StringIO(str(all_el)))[0] if all_el else pd.DataFrame()

    home_el = soup.find("table", {"id": re.compile(f"shots_{home_id}")})
    home_shots = pd.read_html(StringIO(str(home_el)))[0] if home_el else pd.DataFrame()

    away_el = soup.find("table", {"id": re.compile(f"shots_{away_id}")})
    away_shots = pd.read_html(StringIO(str(away_el)))[0] if away_el else pd.DataFrame()

    return {"all": all_shots, "home": home_shots, "away": away_shots}

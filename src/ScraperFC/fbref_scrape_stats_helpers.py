""" Helper functions for fbref.scrape_stats()
"""
import pandas as pd
from io import StringIO
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fbref import FBref

# ==================================================================================================
def _scrape_not_big5_stats(
        self: "FBref", season_url: str, stats_categories: dict, stat_category: str
) -> dict[str, pd.DataFrame]:
    season_url_split = season_url.split("/")
    season_url_split.insert(-1, stats_categories[stat_category]["url"])
    stat_url = "/".join(season_url_split)

    soup = self._get_soup(stat_url)

    squad_tag = soup.find(
        "table", {"id": re.compile(f"{stats_categories[stat_category]['html']}_for")}
    )
    squad_df = pd.read_html(StringIO(str(squad_tag)))[0] if squad_tag else pd.DataFrame()

    opp_tag = soup.find(
        "table", {"id": re.compile(f"{stats_categories[stat_category]['html']}_against")}
    )
    opp_df = pd.read_html(StringIO(str(opp_tag)))[0] if opp_tag else pd.DataFrame()

    player_tag = soup.find("table", {"id": f"stats_{stats_categories[stat_category]['html']}"})
    player_df = pd.read_html(StringIO(str(player_tag)))[0] if player_tag else pd.DataFrame()

    return {"squad": squad_df, "opponent": opp_df, "player": player_df}

# ==================================================================================================
def _scrape_big5_stats(
        self: "FBref", season_url: str, stats_categories: dict, stat_category: str
) -> dict[str, pd.DataFrame]:
    # Build URL to squad stats for the chosen category
    season_url_split = season_url.split("/")
    season_url_split.insert(-1, stats_categories[stat_category]["url"])
    season_url_split.insert(-1, "squads")
    squad_stats_url = "/".join(season_url_split)

    # Get squad stats
    soup = self._get_soup(squad_stats_url)

    squad_tag = soup.find(
        "table", {"id": re.compile(f"{stats_categories[stat_category]['html']}_for")}
    )
    squad_df = pd.read_html(StringIO(str(squad_tag)))[0] if squad_tag else pd.DataFrame()

    opp_tag = soup.find(
        "table", {"id": re.compile(f"{stats_categories[stat_category]['html']}_against")}
    )
    opp_df = pd.read_html(StringIO(str(opp_tag)))[0] if opp_tag else pd.DataFrame()

    # Build URL to player stats
    season_url_split = season_url.split("/")
    season_url_split.insert(-1, stats_categories[stat_category]["url"])
    season_url_split.insert(-1, "players")
    player_stats_url = "/".join(season_url_split)

    # Scrape player stats
    soup = self._get_soup(player_stats_url)

    player_tag = soup.find("table", {"id": f"stats_{stats_categories[stat_category]['html']}"})
    player_df = pd.read_html(StringIO(str(player_tag)))[0] if player_tag else pd.DataFrame()

    return {"squad": squad_df, "opponent": opp_df, "player": player_df}

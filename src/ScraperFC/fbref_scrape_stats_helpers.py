""" Helper functions for fbref.scrape_stats()
"""
import pandas as pd
from io import StringIO
import re
from typing import TYPE_CHECKING
from bs4 import Tag
from .fbref_helpers import _get_ids_from_table, _get_stats_table_tag

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

    # Get the "for" table as df
    squad_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": re.compile(f"{stats_categories[stat_category]['html']}_for")}}
    )
    if isinstance(squad_table_tag, Tag):
        squad_df = pd.read_html(StringIO(str(squad_table_tag)))[0]

        # Add team IDs for the "for" table
        squad_ids = _get_ids_from_table(squad_table_tag, "team")
        squad_df['Team ID'] = squad_ids
    elif squad_table_tag is None:
        print(f'\nWARNING: Squad stats table from {stat_url} is None.')
        squad_df = pd.DataFrame()

    # Get the "against" table as df
    opp_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": re.compile(f"{stats_categories[stat_category]['html']}_against")}}
    )
    if isinstance(opp_table_tag, Tag):
        opp_df = pd.read_html(StringIO(str(opp_table_tag)))[0]

        # Add team IDs for the "against" table
        opps_ids = _get_ids_from_table(opp_table_tag, "team")
        opp_df['Team ID'] = opps_ids
    elif opp_table_tag is None:
        print(f'\nWARNING: Opponent stats table from {stat_url} is None.')
        opp_df = pd.DataFrame()

    # Create player stats df
    player_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": re.compile(f"stats_{stats_categories[stat_category]['html']}")}}
    )
    if isinstance(player_table_tag, Tag):
        player_df = pd.read_html(StringIO(str(player_table_tag)))[0]

        # Add player IDs
        player_ids = _get_ids_from_table(player_table_tag, "player")
        player_df.loc[player_df[('Unnamed: 0_level_0', 'Rk')] != 'Rk', 'Player ID'] = player_ids
    elif player_table_tag is None:
        print(f'\nWARNING: Player stats table from {stat_url} is None.')
        player_df = pd.DataFrame()

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

    squad_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": re.compile(f"{stats_categories[stat_category]['html']}_for")}}
    )
    if isinstance(squad_table_tag, Tag):
        squad_df = pd.read_html(StringIO(str(squad_table_tag)))[0]

        # Add team IDs for squad stats
        squad_ids = _get_ids_from_table(squad_table_tag, "team")
        squad_df['Team ID'] = squad_ids
    elif squad_table_tag is None:
        print(f'\nWARNING: Squad stats table from {squad_stats_url} is None.')
        squad_df = pd.DataFrame()

    # Get opponent stats
    opp_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": re.compile(f"{stats_categories[stat_category]['html']}_against")}}
    )
    if isinstance(opp_table_tag, Tag):
        opp_df = pd.read_html(StringIO(str(opp_table_tag)))[0]

        # Add team IDs for opponent stats
        opp_ids = _get_ids_from_table(opp_table_tag, "team")
        opp_df['Team ID'] = opp_ids
    elif opp_table_tag is None:
        print(f'\nWARNING: Opponent stats table from {squad_stats_url} is None.')
        opp_df = pd.DataFrame()

    # Build URL to player stats
    season_url_split = season_url.split("/")
    season_url_split.insert(-1, stats_categories[stat_category]["url"])
    season_url_split.insert(-1, "players")
    player_stats_url = "/".join(season_url_split)

    # Scrape player stats
    soup = self._get_soup(player_stats_url)

    player_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": f"stats_{stats_categories[stat_category]['html']}"}}
    )
    if isinstance(player_table_tag, Tag):
        player_df = pd.read_html(StringIO(str(player_table_tag)))[0]

        # Add player IDs
        player_ids = _get_ids_from_table(player_table_tag, "player")
        player_df.loc[player_df[('Unnamed: 0_level_0', 'Rk')] != 'Rk', 'Player ID'] = player_ids
    elif player_table_tag is None:
        print(f'\nWARNING: Player stats table from {player_stats_url} is None.')
        player_df = pd.DataFrame()

    return {"squad": squad_df, "opponent": opp_df, "player": player_df}

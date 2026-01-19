""" Helper functions for use in multiple functions in the FBref module
"""
from bs4 import BeautifulSoup, Comment, Tag, NavigableString


# ==================================================================================================
def _get_player_id_from_url(url: str) -> str:
    pieces = url.split("/")
    players_idx = None
    for i, piece in enumerate(pieces):
        if piece == "players":
            players_idx = i
    if players_idx is None:
        raise ValueError(f"'players' chunk not found in split URL {pieces}")
    return pieces[players_idx + 1]

# ==================================================================================================
def _get_team_id_from_url(url: str) -> str:
    pieces = url.split("/")
    squads_idx = None
    for i, piece in enumerate(pieces):
        if piece == "squads":
            squads_idx = i
    if squads_idx is None:
        raise ValueError(f"'squads' chunk not found in split URL {pieces}")
    return pieces[squads_idx + 1]

# ==================================================================================================
def _find_commented_out_tables(soup: BeautifulSoup) -> list[str]:
    comments = soup.find_all(string = lambda el: isinstance(el, Comment))
    table_comments = [c for c in comments if 'table' in c and '<div' in c]
    return table_comments

# ==================================================================================================
def _get_ids_from_table(table_tag: Tag, table_type: str) -> list[str]:
    valid_types = ["team", "player"]
    if table_type not in valid_types:
        raise ValueError(f"Invalid table type: {table_type}. Valid types are {valid_types}")
    rows = table_tag.find_all("tr")
    urls = [el.find("a")["href"] for el in rows if el.find("a")]
    if table_type == "team":
        ids = [_get_team_id_from_url(url) for url in urls]
    elif table_type == "player":
        ids = [_get_player_id_from_url(url) for url in urls]
    return ids

# ==================================================================================================
def _get_stats_table_tag(soup: BeautifulSoup, soup_find_args: dict) -> Tag | NavigableString | None:
    """ Find a stats table in the soup from an FBref page

    If no table is explicity found, will search for a commented out tables. (Champions League
    comments out the player stats table until the user clicks to show the player stats.)

    Params:
        soup
        soup_find_args: dict passed to soup.find(). Will probably be {'name': str, 'attrs': dict}
    """
    table_tag = soup.find(**soup_find_args)

    # If no tag was found, try looking in commented out tables
    if table_tag is None:
        # Try to find commented out table
        table_comments = _find_commented_out_tables(soup)
        for comment in table_comments:
            comment_soup = BeautifulSoup(comment, "html.parser")
            table_tag = comment_soup.find(**soup_find_args)

    return table_tag

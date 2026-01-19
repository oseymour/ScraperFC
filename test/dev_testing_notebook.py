import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from rootutils import find_root
    from io import StringIO
    import pandas as pd
    import random
    import re
    from tqdm import tqdm
    from botasaurus.browser import browser, ElementWithSelectorNotFoundException
    from bs4 import BeautifulSoup, Comment, Tag
    import requests
    import time

    sys.path.append(str(find_root() / "src"))
    import ScraperFC as sfc
    from ScraperFC.fbref_helpers import _get_player_id_from_url, _get_team_id_from_url, _find_commented_out_tables
    from ScraperFC.fbref_scrape_stats_helpers import _get_stats_table_tag
    return re, sfc


@app.cell
def _():
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
    return (stats_categories,)


@app.cell
def _(sfc):
    fb = sfc.FBref()

    url = "https://fbref.com/en/comps/10/2024-2025/stats/2024-2025-Championship-Stats"

    soup = fb._get_soup(url)
    return (soup,)


@app.cell
def _(re, soup, stats_categories):
    stat_category = "standard"

    squad_table_tag = _get_stats_table_tag(
        soup,
        {"name": "table", "attrs": {"id": re.compile(f"{stats_categories[stat_category]['html']}_for")}}
    )

    team_els = squad_table_tag.find_all("tr")
    [
        el.find("a")["href"]
        for el in team_els
        if el.find("a")
    ]
    return


if __name__ == "__main__":
    app.run()

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
    return (sfc,)


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
    return


@app.cell
def _(sfc):
    fb = sfc.FBref()

    year = "1966"
    league = "FIFA World Cup"

    matches = fb.scrape_matches(year, league)
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.19.11"
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
    from datetime import datetime, timezone
    import time

    sys.path.append(str(find_root() / "src"))
    import ScraperFC as sfc
    from ScraperFC.fbref_helpers import _get_player_id_from_url, _get_team_id_from_url, _find_commented_out_tables
    from ScraperFC.fbref_scrape_stats_helpers import _get_stats_table_tag
    from ScraperFC.utils import botasaurus_browser_get_json
    from ScraperFC.sofascore_player import SofascorePlayer
    from ScraperFC.sofascore_helpers import _get_player_career_stats_df

    return (sfc,)


@app.cell
def _(sfc):
    ss = sfc.Sofascore()
    player_details = ss.scrape_player_details(league="France Ligue 1", year="21/22")
    return (player_details,)


@app.cell
def _(player_details):
    player_details[0].career_stats
    return


if __name__ == "__main__":
    app.run()

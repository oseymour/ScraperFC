import marimo

__generated_with = "0.18.4"
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
    from bs4 import BeautifulSoup
    import requests
    import time

    sys.path.append(str(find_root() / "src"))
    import ScraperFC as sfc
    from ScraperFC.fbref import stats_categories
    return (sfc,)


@app.cell
def _(sfc):
    fb = sfc.FBref()

    match_link = "https://fbref.com/en/matches/ba5dd68e/Alaves-Barcelona-October-6-2024-La-Liga"

    match = fb.scrape_match(match_link)
    return (match,)


@app.cell
def _(match):
    match.__dict__
    return


if __name__ == "__main__":
    app.run()

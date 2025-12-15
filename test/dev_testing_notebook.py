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

    sys.path.append(str(find_root() / "src"))
    import ScraperFC as sfc
    from ScraperFC.fbref import stats_categories
    return (sfc,)


@app.cell
def _(sfc):
    self = sfc.FBref()

    league, year = "FBref Big 5 Combined", "2024-2025"
    stat_category = "goalkeeping"

    stats = self.scrape_stats(year, league, stat_category)
    return (stats,)


@app.cell
def _(stats):
    stats["player"]
    return


if __name__ == "__main__":
    app.run()

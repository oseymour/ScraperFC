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
    return (sfc,)


@app.cell
def _(sfc):
    fb = sfc.FBref()
    return (fb,)


@app.cell
def _(fb):
    stats = fb.scrape_all_stats(league="Portugal Primeira Liga", year="2024-2025")
    return (stats,)


@app.cell
def _(stats):
    [stats[k]['player'].shape for k in stats]
    return


if __name__ == "__main__":
    app.run()

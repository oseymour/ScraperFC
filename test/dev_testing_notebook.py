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
    return (sfc,)


@app.cell
def _(sfc):
    fb = sfc.FBref()

    matches = fb.scrape_matches(league="UEFA European Championship", year="2008")
    return (matches,)


@app.cell
def _(matches):
    matches
    return


if __name__ == "__main__":
    app.run()

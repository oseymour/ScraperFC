import marimo

__generated_with = "0.10.19"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    sys.path.append("../src")  # import local scraperfc
    import ScraperFC as sfc

    from tqdm import tqdm
    import random
    return random, sfc, sys, tqdm


@app.cell
def _(random, sfc, tqdm):
    from ScraperFC.fbref import comps

    fb = sfc.FBref()

    for league in comps.keys():
        valid_years = fb.get_valid_seasons(league)
        for year in valid_years:
            match_links = fb.get_match_links(year, league)
            match_links = random.sample(match_links, len(match_links) // 10)
            for link in tqdm(match_links, desc=f"{year} {league}"):
                _ = fb.scrape_match(link)
    return comps, fb, league, link, match_links, valid_years, year


if __name__ == "__main__":
    app.run()

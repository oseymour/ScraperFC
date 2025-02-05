import marimo

__generated_with = "0.10.19"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    sys.path.append("../src")
    import ScraperFC as sfc
    return sfc, sys


@app.cell
def _(sfc):
    tm = sfc.Transfermarkt()
    return (tm,)


@app.cell
def _():
    league = "Turkish Super Lig"
    return (league,)


@app.cell
def _(league, tm):
    tm.get_valid_seasons(league)
    return


@app.cell
def _():
    year = "24/25"
    return (year,)


@app.cell
def _(league, tm, year):
    tm.get_club_links(year, league)
    return


@app.cell
def _(league, tm, year):
    tm.get_match_links(year, league)
    return


@app.cell
def _(league, tm, year):
    tm.get_player_links(year, league)
    return


@app.cell
def _(league, tm, year):
    tm.scrape_players(year, league)
    return


if __name__ == "__main__":
    app.run()

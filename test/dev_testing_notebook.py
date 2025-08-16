import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from rootutils import find_root

    sys.path.append(str(find_root() / "src"))
    import ScraperFC as sfc
    return (sfc,)


@app.cell
def _(sfc):
    ss = sfc.Sofascore()

    ss.scrape_team_league_stats("2023", "CONCACAF Gold Cup")
    return


if __name__ == "__main__":
    app.run()

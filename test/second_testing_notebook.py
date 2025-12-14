import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys

    sys.path.append("../src")  # import local scraperfc
    import ScraperFC as sfc
    return (sfc,)


@app.cell
def _(sfc):
    ss = sfc.Sofascore()

    ss.get_valid_seasons("Saudi Arabia Pro League")
    return


if __name__ == "__main__":
    app.run()

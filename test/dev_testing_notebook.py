import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from rootutils import find_root
    from cloudscraper import CloudScraper
    from bs4 import BeautifulSoup

    sys.path.append(str(find_root() / "src"))
    import ScraperFC as sfc
    return (sfc,)


@app.cell
def _(sfc):
    sfc.utils.get_module_comps("FBref")
    return


if __name__ == "__main__":
    app.run()

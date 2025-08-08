import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    sys.path.append("../src")
    import ScraperFC as sfc
    return (sfc,)


@app.cell
def _(sfc):
    from ScraperFC.sofascore import API_PREFIX, comps

    ss = sfc.Sofascore()

    league = "EPL"
    year = "24/25"
    match_id = 61627

    match_id = ss._check_and_convert_match_id(match_id)
    url = f"{API_PREFIX}/event/{match_id}/lineups"

    response = sfc.utils.botasaurus_browser_get_json(url)
    # response = sfc.utils.botasaurus_request_get_json(url)
    return (response,)


@app.cell
def _(response):
    response['error']
    return


if __name__ == "__main__":
    app.run()

from botasaurus.request import request, Request
from botasaurus.browser import browser, Driver
import json

@request(output=None, create_error_logs=False)
def botasaurus_request_get_json(request: Request, url: str) -> dict:
    """ Use Botasaurus REQUESTS module to get JSON from page.

    Parameters
    ----------
    request : botasaurus.request.Request
        The request object provided by the botasaurus decorator
    url : str
        The URL to request

    Returns
    -------
    dict
    """
    if not isinstance(url, str):
        raise TypeError('`url` must be a string.')
    response = request.get(url)
    result = response.json()
    return result

@browser(headless=True, output=None, create_error_logs=False, block_images_and_css=True)
def botasaurus_browser_get_json(driver: Driver, url: str) -> dict:
    """ Use Botasaurus BROWSER model to get JSON from page

    Parameters
    ----------
    driver : botasaurus.browser.Driver
        Browser object. Provided by Botasaurus decorator
    url : str
        The URL to scrape

    Returns
    -------
    dict
    """
    driver.get(url)
    page_source = driver.page_text
    result = json.loads(page_source)
    return result

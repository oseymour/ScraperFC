from botasaurus.request import request
from botasaurus.browser import browser
import json
from bs4 import BeautifulSoup
import time


# ==================================================================================================
def botasaurus_request_get_json(url: str, delay: int = 0) -> dict:
    """Use Botasaurus REQUESTS module to get JSON from page.

    :param url: The URL to request
    :type url: str
    :param delay: Seconds to wait after the request (default: 0)
    :type delay: int

    :rtype: dict
    """
    if not isinstance(url, str):
        raise TypeError("`url` must be a string.")
    if not isinstance(delay, int):
        raise TypeError("`delay` must be an int.")
    if delay < 0:
        raise ValueError("`delay` must be non-negative.")

    @request(output=None, create_error_logs=False)
    def _get_json(request, url):  # type: ignore
        response = request.get(url)
        if delay > 0:
            time.sleep(delay)
        return response.json()

    return _get_json(url)

# ==================================================================================================
def botasaurus_browser_get_json(
        url: str, headless: bool = True, block_images_and_css: bool = True,
        wait_for_complete_page_load: bool = True, delay: int = 0
) -> dict:
    """Use Botasaurus BROWSER module to get JSON from page

    :param url: The URL to scrape
    :type url: str
    :param headless: Whether to run the browser in headless mode
    :type headless: bool
    :param block_images_and_css: Whether to block images and CSS
    :type block_images_and_css: bool
    :param wait_for_complete_page_load: Whether to wait for the page to load completely
    :type wait_for_complete_page_load: bool
    :param delay: Seconds to wait after the request (default: 0)
    :type delay: int

    :rtype: dict
    """
    if not isinstance(url, str):
        raise TypeError("`url` must be a string.")
    if not isinstance(headless, bool):
        raise TypeError("`headless` must be a bool.")
    if not isinstance(block_images_and_css, bool):
        raise TypeError("`block_images_and_css` must be a bool.")
    if not isinstance(wait_for_complete_page_load, bool):
        raise TypeError("`wait_for_complete_page_load` must be a bool.")
    if not isinstance(delay, int):
        raise TypeError("`delay` must be an int.")
    if delay < 0:
        raise ValueError("`delay` must be non-negative.")

    @browser(
        headless=headless, block_images_and_css=block_images_and_css,
        wait_for_complete_page_load=wait_for_complete_page_load,
        output=None, create_error_logs=False
    )
    def _get_json(driver, url):  # type: ignore
        driver.get(url)
        if delay > 0:
            time.sleep(delay)
        return json.loads(driver.page_text)

    return _get_json(url)

# ==================================================================================================
def botasaurus_request_get_soup(url: str, delay: int = 0) -> BeautifulSoup:
    """Use Botasaurus REQUESTS module to get Soup from page.

    :param url: The URL to request
    :type url: str
    :param delay: Seconds to wait after the request (default: 0)
    :type delay: int

    :rtype: bs4.BeautifulSoup
    """
    if not isinstance(url, str):
        raise TypeError("`url` must be a string.")
    if not isinstance(delay, int):
        raise TypeError("`delay` must be an int.")
    if delay < 0:
        raise ValueError("`delay` must be non-negative.")

    @request(output=None, create_error_logs=False)
    def _get_soup(request, url):  # type: ignore
        response = request.get(url)
        if delay > 0:
            time.sleep(delay)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

    return _get_soup(url)

# ==================================================================================================
def botasaurus_browser_get_soup(
        url: str, headless: bool = False, block_images_and_css: bool = False,
        wait_for_complete_page_load: bool = True, delay: int = 0
) -> BeautifulSoup:
    """ Use Botasaurus BROWSER module to get Soup from page.

    :param url: The URL to scrape
    :type url: str
    :param headless: Whether to run the browser in headless mode
    :type headless: bool
    :param block_images_and_css: Whether to block images and CSS
    :type block_images_and_css: bool
    :param wait_for_complete_page_load: Whether to wait for the page to load completely
    :type wait_for_complete_page_load: bool
    :param delay: Seconds to wait after the request (default: 0)
    :type delay: int

    :rtype: bs4.BeautifulSoup
    """
    if not isinstance(url, str):
        raise TypeError("`url` must be a string.")
    if not isinstance(headless, bool):
        raise TypeError("`headless` must be a bool.")
    if not isinstance(block_images_and_css, bool):
        raise TypeError("`block_images_and_css` must be a bool.")
    if not isinstance(wait_for_complete_page_load, bool):
        raise TypeError("`wait_for_complete_page_load` must be a bool.")
    if not isinstance(delay, int):
        raise TypeError("`delay` must be an int.")
    if delay < 0:
        raise ValueError("`delay` must be non-negative.")

    @browser(
        headless=headless, block_images_and_css=block_images_and_css,
        wait_for_complete_page_load=wait_for_complete_page_load,
        output=None, create_error_logs=False
    )
    def _get_soup(driver, url):  # type: ignore
        driver.get(url)
        if delay > 0:
            time.sleep(delay)
        return BeautifulSoup(driver.page_html, "html.parser")

    return _get_soup(url)

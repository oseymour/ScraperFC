from botasaurus.request import request
from botasaurus.browser import browser
import json
import sys
from bs4 import BeautifulSoup
import time

# Chrome flags required when running as root (e.g. inside a Docker container on Linux)
_LINUX_CHROME_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]


# ==================================================================================================
def botasaurus_request_get_json(url: str, delay: int = 0) -> dict:
    """Use Botasaurus REQUESTS module to get JSON from page.

    :param url: The URL to request
    :type url: str
    :param delay: Seconds to wait after the request (default: 0)
    :type delay: int
    :raises TypeError: If any of the parameters are the wrong type
    :raises ValueError: If ``delay`` is negative
    :return: JSON data
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
def _validate_browser_get_json_args(
        url: str, headless: bool, block_images_and_css: bool,
        wait_for_complete_page_load: bool, delay: int,
        via_xhr: bool, warm_url: str | None, add_arguments: list[str] | None,
) -> None:
    """
    Validate arguments for :func:`botasaurus_browser_get_json`.

    :raises TypeError: If any argument is the wrong type.
    :raises ValueError: If ``delay`` is negative, or ``via_xhr=True`` without ``warm_url``.
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
    if not isinstance(via_xhr, bool):
        raise TypeError("`via_xhr` must be a bool.")
    if warm_url is not None and not isinstance(warm_url, str):
        raise TypeError("`warm_url` must be a string or None.")
    if via_xhr and warm_url is None:
        raise ValueError("`warm_url` is required when `via_xhr=True`.")
    if add_arguments is not None and not isinstance(add_arguments, list):
        raise TypeError("`add_arguments` must be a list of strings or None.")


# ==================================================================================================
def botasaurus_browser_get_json(
        url: str, headless: bool = True, block_images_and_css: bool = True,
        wait_for_complete_page_load: bool = True, delay: int = 0,
        via_xhr: bool = False, warm_url: str | None = None,
        add_arguments: list[str] | None = None,
) -> dict:
    """
    Use Botasaurus BROWSER module to get JSON from a page.

    Two modes:

    * **Direct navigation** (default): navigate to ``url`` and parse the page text
      as JSON.
    * **In-page XHR** (``via_xhr=True``): navigate to ``warm_url`` first to
      establish a session and pass any anti-bot challenge, then issue a
      synchronous ``XMLHttpRequest`` to ``url`` from that page, sending the
      ``X-Requested-With: XMLHttpRequest`` header that single-page-app backends
      expect. ``warm_url`` is required in this mode and ``headless`` must be
      ``False`` for the challenge to resolve. ``delay`` is the post-warm-up wait.

    :param url: The URL to scrape.
    :type url: str
    :param headless: Whether to run the browser in headless mode.
    :type headless: bool
    :param block_images_and_css: Whether to block images and CSS.
    :type block_images_and_css: bool
    :param wait_for_complete_page_load: Whether to wait for the page to load completely.
    :type wait_for_complete_page_load: bool
    :param delay: Seconds to wait after navigation (default: 0). In ``via_xhr``
        mode this is the wait between loading ``warm_url`` and issuing the XHR.
    :type delay: int
    :param via_xhr: Fetch ``url`` as an in-page XHR from ``warm_url`` instead of
        navigating to it directly.
    :type via_xhr: bool
    :param warm_url: Origin page to load before the XHR. Required when
        ``via_xhr=True``; ignored otherwise.
    :type warm_url: str | None
    :raises TypeError: If any of the parameters are the wrong type.
    :raises ValueError: If ``delay`` is negative, or ``via_xhr=True`` without ``warm_url``.
    :return: JSON data.
    :rtype: dict
    """
    _validate_browser_get_json_args(
        url, headless, block_images_and_css, wait_for_complete_page_load,
        delay, via_xhr, warm_url, add_arguments,
    )

    _browser_kwargs: dict = dict(
        headless=headless, block_images_and_css=block_images_and_css,
        wait_for_complete_page_load=wait_for_complete_page_load,
        output=None, create_error_logs=False,
    )
    if add_arguments:
        _browser_kwargs["add_arguments"] = add_arguments

    @browser(**_browser_kwargs)
    def _get_json(driver, target):  # type: ignore
        """Fetch JSON from ``target``, optionally via warm-session XHR."""
        if via_xhr:
            driver.get(warm_url)    # load origin page to set session cookies
            if delay > 0:
                time.sleep(delay)   # wait for the challenge to resolve
            js = f"""
            var xhr = new XMLHttpRequest();
            xhr.open('GET', {json.dumps(target)}, false);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.send();
            return JSON.parse(xhr.responseText);
            """
            return driver.run_js(js)
        driver.get(target)
        if delay > 0:
            time.sleep(delay)
        return json.loads(driver.page_text)

    return _get_json(url)


# ==================================================================================================
def botasaurus_browser_get_json_via_xhr(
        url: str, warm_url: str, headless: bool = True, delay: int = 6,
        block_images_and_css: bool = True,
        add_arguments: list[str] | None = None,
) -> dict:
    """
    Fetch a JSON API endpoint that sits behind a browser/bot challenge.

    Warms a browser session on ``warm_url`` then issues an in-page XHR to ``url``.
    Generic: any challenge-blocked source can use it by passing its own origin as
    ``warm_url`` (e.g. ``"https://fbref.com/"``).

    ``block_images_and_css=True`` (the default) is recommended: it reduces page-load
    time during the warm-up, allowing the challenge to resolve before the browser
    times out.

    On Linux (e.g. inside a Docker container), ``--no-sandbox`` and
    ``--disable-dev-shm-usage`` are added automatically so Chrome can run as root.

    :param url: API endpoint to fetch.
    :type url: str
    :param warm_url: Origin page to load first to acquire session cookies.
    :type warm_url: str
    :param headless: Whether to run the browser in headless mode (default: True).
    :type headless: bool
    :param delay: Seconds to wait after warming before the XHR (default: 6).
    :type delay: int
    :param block_images_and_css: Whether to block images and CSS (default: True).
    :type block_images_and_css: bool
    :param add_arguments: Extra Chrome command-line flags (default: None).
    :type add_arguments: list[str] | None
    :return: JSON data.
    :rtype: dict
    """
    args = list(add_arguments) if add_arguments else []
    if sys.platform == "linux":
        for flag in _LINUX_CHROME_ARGS:
            if flag not in args:
                args.append(flag)
    return botasaurus_browser_get_json(
        url, via_xhr=True, warm_url=warm_url,
        headless=headless, delay=delay, block_images_and_css=block_images_and_css,
        add_arguments=args or None,
    )

# ==================================================================================================
def botasaurus_request_get_soup(url: str, delay: int = 0) -> BeautifulSoup:
    """Use Botasaurus REQUESTS module to get Soup from page.

    :param url: The URL to request
    :type url: str
    :param delay: Seconds to wait after the request (default: 0)
    :type delay: int
    :raises TypeError: If any of the parameters are the wrong type
    :raises ValueError: If ``delay`` is negative
    :return: BeautifulSoup object
    :rtype: BeautifulSoup
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
    :raises TypeError: If any of the parameters are the wrong type
    :raises ValueError: If ``delay`` is negative
    :return: BeautifulSoup object
    :rtype: BeautifulSoup
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

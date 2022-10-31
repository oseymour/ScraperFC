from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from IPython.display import clear_output
import random
import pandas as pd
import numpy as np

# Dict of data sources, leagues, and the first year data is available for that league from that source
# Only used by check_season(), but moved here to be able to be accessed when ScraperFC is imported
valid_years = {
        'All': {},
        'FBRef': {
            # Men's big 5
            # Other mens's domestic leagues
            # Men's international cups
            # Men's domstic cups
            # Women's domestic leagues
            # Women's international cups
            # Women's domestic leagues
            "Women World Cup": 1991,
            "World Cup": 1930,
            "Copa America": 2015,
            "Copa Libertadores": 2014,
            "Champions League": 1991,
            "Europa Conference League": 2022,
            "Europa League": 1991,
            "Euros": 2000,
            "Women Champions League": 2015,
            "Women Euros": 2001,
            "MLS": 1996,
            "NWSL": 2013,
            "A-League Women": 2019,
            "Brazilian Serie A": 2014,
            "Eredivisie": 2001,
            "EFL Championship": 2002,
            "EPL": 1993,
            "WSL": 2017,
            "Women Ligue 1": 2018,
            "Ligue 1": 1996,
            "Bundesliga": 1989,
            "Women Bundesliga": 2017,
            "Women Serie A": 2019,
            "Serie A": 1989,
            "Liga MX": 2004,
            "NWSL Challenge Cup": 2020,
            "NWSL Fall Series": 2020,
            "Primeira Liga": 2001,
            "La Liga": 1989,
            "Liga F": 2023,
        },
        'Understat': {
            'EPL': 2015,
            'La Liga': 2015,
            'Bundesliga': 2015,
            'Serie A': 2015,
            'Ligue 1': 2015,
        },
        'FiveThirtyEight': {
            'EPL': 2017,
            'La Liga': 2017,
            'Bundesliga': 2017,
            'Serie A': 2017,
            'Ligue 1': 2017,
        },
        'SofaScore': {'USL League One': 2019,},
        'Capology': {
            'Bundesliga': 2014,
            '2.Bundesliga': 2020,
            'EPL': 2014,
            'EFL Championship': 2014,
            'Serie A': 2010,
            'Serie B': 2020,
            'La Liga': 2014,
            'La Liga 2': 2020,
            'Ligue 1': 2014,
            'Ligue 2': 2020,
            'Eredivisie': 2014,
            'Primeira Liga': 2014,
            'Scottish PL': 2020,
            'Super Lig': 2014,
            'Belgian 1st Division': 2014,
        },
        'Transfermarkt': {
            'EPL': 1993,
            'EFL Championship': 2005,
            'EFL1': 2005,
            'EFL2': 2005,
            'Bundesliga': 1964,
            '2.Bundesliga': 1982,
            'Serie A': 1930,
            'Serie B': 1930,
            'La Liga': 1929,
            'La Liga 2': 1929,
            'Ligue 1': 1970,
            'Ligue 2': 1993,
            'Eredivisie': 1955,
            'Scottish PL': 2004,
            'Super Lig': 1960,
            'Jupiler Pro League': 1987,
            'Liga Nos': 1994,
            'Russian Premier League': 2011,
            'Brasileirao': 2001,
            'Argentina Liga Profesional': 2015,
            'MLS': 1996,
        },
    }

################################################################################
def check_season(year, league, source):
    """ Checks to make sure that the given league season is a valid season for\
        the scraper.
    
    Args
    ----
    year : int
        Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
    league : str
        League. Look in shared_functions.py for the available leagues for each\
        module.
    source : str
        The scraper to be checked (e.g. "FBRef", "Transfermarkt, etc.). These\
        are the ScraperFC modules.
    Returns
    -------
    err : str
        String of the error message, if there is one.
    valid : bool
        True if the league season is valid for the scraper. False otherwise.
    """
    assert source in list(valid_years.keys())
    error = None
    
    # make sure year is an int
    if type(year) != int:
        error = "Year needs to be an integer."
        return error, False
    
    # Make sure league is a valid string for the source
    if type(league)!=str or league not in list(valid_years[source].keys()):
        error = f'League must be a string. Options are {list(valid_years[source].keys())}'
        return error, False
    
    # Make sure the source has data from the requested league and year
    if year < valid_years[source][league]:
        error = f'{year} invalid for source {source} and league {league}. Must be {valid_years[source][league]} or later.'
        return error, False
    
    return error, True

################################################################################
def get_proxy():
    """ Gets a proxy address.

    Can be used to initialize a Selenium WebDriver to change the address of the\
    browser. Adapted from https://stackoverflow.com/questions/59409418/how-to-rotate-selenium-webrowser-ip-address.\
    Randomly chooses one proxy.
    
    Returns
    -------
    proxy : str
        In the form <IP address>:<port>
    """
    options = Options()
    options.headless = True
    options.add_argument('window-size=700,600')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    clear_output()
    
    try:
        driver.get('https://sslproxies.org/')
        table = driver.find_elements(By.TAG_NAME, 'table')[0]
        df = pd.read_html(table.get_attribute('outerHTML'))[0]
        df = df.iloc[np.where(~np.isnan(df['Port']))[0],:] # ignore nans

        ips = df['IP Address'].values
        ports = df['Port'].astype('int').values

        driver.quit()
        proxies = list()
        for i in range(len(ips)):
            proxies.append("{}:{}".format(ips[i], ports[i]))
        i = random.randint(0, len(proxies)-1)
        return proxies[i]
    except Exception as e:
        driver.close()
        driver.quit()
        raise e
        
################################################################################
def xpath_soup(element):
    """ Generate xpath from BeautifulSoup4 element.
    
    I shamelessly stole this from https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf.
    
    Args
    ----
    element : bs4.element.Tag or bs4.element.NavigableString
        BeautifulSoup4 element.
    Returns
    -------
    : str
        xpath as string
    Usage
    -----
    >>> import bs4
    >>> html = (
    ...     '<html><head><title>title</title></head>'
    ...     '<body><p>p <i>1</i></p><p>p <i>2</i></p></body></html>'
    ...     )
    >>> soup = bs4.BeautifulSoup(html, 'html.parser')
    >>> xpath_soup(soup.html.body.p.i)
    '/html/body/p[1]/i'
    >>> import bs4
    >>> xml = '<doc><elm/><elm/></doc>'
    >>> soup = bs4.BeautifulSoup(xml, 'lxml-xml')
    >>> xpath_soup(soup.doc.elm.next_sibling)
    '/doc/elm[2]'
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
                )
            )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)

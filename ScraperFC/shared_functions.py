from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from IPython.display import clear_output
import random
import pandas as pd
import numpy as np

# Dict of data sources and leagues for each source
sources = {
    'All': {},
    'FBRef': {
        # Each competition gets its first valid year (from the competition seasons history page on fbref), the url
        # to the season history page, and the 'finder' which is used to find the season and match links in HTML
        #################################
        # Men's club international cups #
        #################################
        'Copa Libertadores': {
            'first valid year': 2014,
            'url': 'https://fbref.com/en/comps/14/history/Copa-Libertadores-Seasons',
            'finder': ['Copa-Libertadores'],
        },
        'Champions League': {
            'first valid year': 1991,
            'url': 'https://fbref.com/en/comps/8/history/Champions-League-Seasons',
            'finder': ['European-Cup', 'Champions-League'],
        },
        'Europa League': {
            'first valid year': 1991,
            'url': 'https://fbref.com/en/comps/19/history/Europa-League-Seasons',
            'finder': ['UEFA-Cup', 'Europa-League'],
        },
        'Europa Conference League': {
            'first valid year': 2022,
            'url': 'https://fbref.com/en/comps/882/history/Europa-Conference-League-Seasons',
            'finder': ['Europa-Conference-League'],
        },
        ####################################
        # Men's national team competitions #
        ####################################
        'World Cup': {
            'first valid year': 1930,
            'url': 'https://fbref.com/en/comps/1/history/World-Cup-Seasons',
            'finder': ['World-Cup'],
        },
        'Copa America': {
            'first valid year': 2015,
            'url': 'https://fbref.com/en/comps/685/history/Copa-America-Seasons',
            'finder': ['Copa-America'],
        },
        'Euros': {
            'first valid year': 2000,
            'url': 'https://fbref.com/en/comps/676/history/European-Championship-Seasons',
            'finder': ['UEFA-Euro', 'European-Championship'],
        },
        ###############
        # Men's big 5 #
        ###############
        'Big 5 combined': {
            'first valid year': 1996,
            'url': 'https://fbref.com/en/comps/Big5/history/Big-5-European-Leagues-Seasons',
            'finder': ['Big-5-European-Leagues'],
        },
        'EPL': {
            'first valid year': 1993,
            'url': 'https://fbref.com/en/comps/9/history/Premier-League-Seasons',
            'finder': ['Premier-League'],
        },
        'Ligue 1': {
            'first valid year': 1996,
            'url': 'https://fbref.com/en/comps/13/history/Ligue-1-Seasons',
            'finder': ['Ligue-1', 'Division-1'],
        },
        'Bundesliga': {
            'first valid year': 1989,
            'url': 'https://fbref.com/en/comps/20/history/Bundesliga-Seasons',
            'finder': ['Bundesliga'],
        },
        'Serie A': {
            'first valid year': 1989,
            'url': 'https://fbref.com/en/comps/11/history/Serie-A-Seasons',
            'finder': ['Serie-A'],
        },
        'La Liga': {
            'first valid year': 1989,
            'url': 'https://fbref.com/en/comps/12/history/La-Liga-Seasons',
            'finder': ['La-Liga'],
        },
        #####################################
        # Men's domestic leagues - 1st tier #
        #####################################
        'MLS': {
            'first valid year': 1996,
            'url': 'https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons',
            'finder': ['Major-League-Soccer'],
        },
        'Brazilian Serie A': {
            'first valid year': 2014,
            'url': 'https://fbref.com/en/comps/24/history/Serie-A-Seasons',
            'finder': ['Serie-A'],
        },
        'Eredivisie': {
            'first valid year': 2001,
            'url': 'https://fbref.com/en/comps/23/history/Eredivisie-Seasons',
            'finder': ['Eredivisie'],
        },
        'Liga MX': {
            'first valid year': 2004,
            'url': 'https://fbref.com/en/comps/31/history/Liga-MX-Seasons',
            'finder': ['Primera-Division', 'Liga-MX'],
        },
        'Primeira Liga': {
            'first valid year': 2001,
            'url': 'https://fbref.com/en/comps/32/history/Primeira-Liga-Seasons',
            'finder': ['Primeira-Liga'],
        },
        ####################################
        # Men's domestic league - 2nd tier #
        ####################################
        'EFL Championship': {
            'first valid year': 2002,
            'url': 'https://fbref.com/en/comps/10/history/Championship-Seasons',
            'finder': ['First-Division', 'Championship'],
        },
        ##############################################
        # Men's domestic league - 3rd tier and lower #
        ##############################################
        #######################
        # Men's domestic cups #
        #######################
        #########################################
        # Women's internation club competitions #
        #########################################
        'Women Champions League': {
            'first valid year': 2015,
            'url': 'https://fbref.com/en/comps/181/history/Champions-League-Seasons',
            'finder': ['Champions-League'],
        },
        ######################################
        # Women's national team competitions #
        ######################################
        'Womens World Cup': {
            'first valid year': 1991,
            'url': 'https://fbref.com/en/comps/106/history/Womens-World-Cup-Seasons',
            'finder': ['Womens-World-Cup'],
        },
        'Womens Euros': {
            'first valid year': 2001,
            'url': 'https://fbref.com/en/comps/162/history/UEFA-Womens-Euro-Seasons',
            'finder': ['UEFA-Womens-Euro'],
        },
        ############################
        # Women's domestic leagues #
        ############################
        'NWSL': {
            'first valid year': 2013,
            'url': 'https://fbref.com/en/comps/182/history/NWSL-Seasons',
            'finder': ['NWSL'],
        },
        'A-League Women': {
            'first valid year': 2019,
            'url': 'https://fbref.com/en/comps/196/history/A-League-Women-Seasons',
            'finder': ['A-League-Women', 'W-League'],
        },
        'WSL': {
            'first valid year': 2017,
            'url': 'https://fbref.com/en/comps/189/history/Womens-Super-League-Seasons',
            'finder': ['Womens-Super-League'],
        },
        'D1 Feminine': {
            'first valid year': 2018,
            'url': 'https://fbref.com/en/comps/193/history/Division-1-Feminine-Seasons',
            'finder': ['Division-1-Feminine'],
        },
        'Womens Bundesliga': {
            'first valid year': 2017,
            'url': 'https://fbref.com/en/comps/183/history/Frauen-Bundesliga-Seasons',
            'finder': ['Frauen-Bundesliga'],
        },
        'Womens Serie A': {
            'first valid year': 2019,
            'url': 'https://fbref.com/en/comps/208/history/Serie-A-Seasons',
            'finder': ['Serie-A'],
        },
        'Liga F': {
            'first valid year': 2023,
            'url': 'https://fbref.com/en/comps/230/history/Liga-F-Seasons',
            'finder': ['Liga-F'],
        },
        #########################
        # Women's domestic cups #
        #########################
        'NWSL Challenge Cup': {
            'first valid year': 2020,
            'url': 'https://fbref.com/en/comps/881/history/NWSL-Challenge-Cup-Seasons',
            'finder': ['NWSL-Challenge-Cup'],
        },
        'NWSL Fall Series': {
            'first valid year': 2020,
            'url': 'https://fbref.com/en/comps/884/history/NWSL-Fall-Series-Seasons',
            'finder': ['NWSL-Fall-Series'],
        },
    },
    'Understat': {
        'EPL': {'first valid year': 2015,},
        'La Liga': {'first valid year': 2015,},
        'Bundesliga':  {'first valid year': 2015,},
        'Serie A':  {'first valid year': 2015,},
        'Ligue 1':  {'first valid year': 2015,},
        'RFPL':  {'first valid year': 2015,},
    },
    'FiveThirtyEight': {
        'EPL':  {'first valid year': 2017,},
        'La Liga':  {'first valid year': 2017,},
        'Bundesliga':  {'first valid year': 2017,},
        'Serie A':  {'first valid year': 2017,},
        'Ligue 1':  {'first valid year': 2017,},
    },
    'SofaScore': {'USL League One':  {'first valid year': 2019,}},
    'Capology': {
        'Bundesliga':  {'first valid year': 2014,},
        '2.Bundesliga':  {'first valid year': 2020,},
        'EPL':  {'first valid year': 2014,},
        'EFL Championship':  {'first valid year': 2014,},
        'Serie A':  {'first valid year': 2010,},
        'Serie B':  {'first valid year': 2020,},
        'La Liga':  {'first valid year': 2014,},
        'La Liga 2':  {'first valid year': 2020,},
        'Ligue 1':  {'first valid year': 2014,},
        'Ligue 2':  {'first valid year': 2020,},
        'Eredivisie':  {'first valid year': 2014,},
        'Primeira Liga':  {'first valid year': 2014,},
        'Scottish PL':  {'first valid year': 2020,},
        'Super Lig':  {'first valid year': 2014,},
        'Belgian 1st Division':  {'first valid year': 2014,},
    },
    'Transfermarkt': {
        'EPL':  {'first valid year': 1993,},
        'EFL Championship': {'first valid year': 2005,},
        'EFL1': {'first valid year': 2005,},
        'EFL2': {'first valid year': 2005,},
        'Bundesliga': {'first valid year': 1964,},
        '2.Bundesliga': {'first valid year': 1982,},
        'Serie A': {'first valid year': 1930,},
        'Serie B': {'first valid year': 1930,},
        'La Liga': {'first valid year': 1929,},
        'La Liga 2': {'first valid year': 1929,},
        'Ligue 1': {'first valid year': 1970,},
        'Ligue 2': {'first valid year': 1993,},
        'Eredivisie': {'first valid year': 1955,},
        'Scottish PL': {'first valid year': 2004,},
        'Super Lig': {'first valid year': 1960,},
        'Jupiler Pro League': {'first valid year': 1987,},
        'Liga Nos': {'first valid year': 1994,},
        'Russian Premier League': {'first valid year': 2011,},
        'Brasileirao': {'first valid year': 2001,},
        'Argentina Liga Profesional': {'first valid year': 2015,},
        'MLS': {'first valid year': 1996,},
    },
}

########################################################################################################################
class InvalidSourceException(Exception):
    ''' Raised when an invalid source is used with the check_season() function.
    '''
    def __init__(self, source):
        super().__init__()
        self.source = source
    def __str__(self):
        return f'{self.source} is not a valid source. Must be one of {list(sources.keys())}.'

########################################################################################################################
class InvalidLeagueException(Exception):
    ''' Raised when an invalid league is used with the check_season() function.
    '''
    def __init__(self, league, source):
        super().__init__()
        self.league = league
        self.source = source
    def __str__(self):
        return f'{self.league} is not a valid league for {self.source}. Options are {list(sources[self.source].keys())}.'

########################################################################################################################
class InvalidYearException(Exception):
    ''' Raised when an invalid year is used with the check_season() function.
    '''
    def __init__(self, year, league, source):
        super().__init__()
        self.year = year
        self.league = league
        self.source = source
    def __str__(self):
        return f'{self.year} invalid for source {self.source} and league {self.league}. ' +\
            f'Must be {sources[self.source][self.league]["first valid year"]} or later.'

########################################################################################################################
class InvalidCurrencyException(Exception):
    ''' Raised when an invalid currency is used with the Capology module.
    '''
    def __init__(self):
        super().__init__()
    def __str__():
        return 'Currency must be one of "eur", "gbp", or "usd".'

########################################################################################################################
class UnavailableSeasonException(Exception):
    ''' Raised when a given year and league is unavailable from a source.
    '''
    def __init__(self, year, league, source):
        super().__init__()
        self.year = year
        self.league = league
        self.source = source
    def __str__(self):
        return f'No {self.league} {self.year} season is available on {self.source}.'

########################################################################################################################
class NoMatchLinksException(Exception):
    ''' Raised when no match links are found
    '''
    def __init__(self, fixtures_url, year, league):
        super().__init__()
        self.fixtures_url = fixtures_url
        self.league = league
        self.year = year
    def __str__(self):
        return f'No match score elements with links found at {self.fixtures_url} for {self.year} {self.league}.'

########################################################################################################################
def check_season(year, league, source):
    ''' Checks to make sure that the given league season is a valid season for the scraper.
    
    Args
    ----
    year : int
        Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
    league : str
        League. Look in shared_functions.py for the available leagues for each\
        module.
    source : str
        The scraper to be checked (e.g. 'FBRef', 'Transfermarkt, etc.). These\
        are the ScraperFC modules.
    Returns
    -------
    err : str
        String of the error message, if there is one.
    valid : bool
        True if the league season is valid for the scraper. False otherwise.
    '''
    # Check source
    if source not in list(sources.keys()):
        raise InvalidSourceException(source)

    # Check league
    if type(league)!=str:
        raise TypeError('League must be a string.')
    if league not in list(sources[source].keys()):
        raise InvalidLeagueException(league, source)
    
    # Check year
    if type(year) != int:
        raise TypeError('Year must be an integer.')
    if year < sources[source][league]['first valid year']:
        raise InvalidYearException(year, league, source)
    
    return

########################################################################################################################
def get_proxy():
    ''' Gets a proxy address.

    Can be used to initialize a Selenium WebDriver to change the address of the\
    browser. Adapted from https://stackoverflow.com/questions/59409418/how-to-rotate-selenium-webrowser-ip-address.\
    Randomly chooses one proxy.
    
    Returns
    -------
    proxy : str
        In the form <IP address>:<port>
    '''
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
            proxies.append('{}:{}'.format(ips[i], ports[i]))
        i = random.randint(0, len(proxies)-1)
        return proxies[i]
    except Exception as e:
        driver.close()
        driver.quit()
        raise e
        
########################################################################################################################
def xpath_soup(element):
    ''' Generate xpath from BeautifulSoup4 element.
    
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
    '''
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

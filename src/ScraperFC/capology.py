from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import requests
from bs4 import BeautifulSoup
from ScraperFC.scraperfc_exceptions import InvalidCurrencyException, InvalidLeagueException, \
    InvalidYearException
from io import StringIO
from typing import Sequence

comps = {
    "Bundesliga":  {'url': 'de/1-bundesliga'},
    "2.Bundesliga":  {'url': 'de/2-bundesliga'},
    "EPL":  {'url': 'uk/premier-league'},
    "EFL Championship":  {'url': 'uk/championship'},
    "Serie A":  {'url': 'it/serie-a'},
    "Serie B":  {'url': 'it/serie-b'},
    "La Liga":  {'url': 'es/la-liga'},
    "La Liga 2":  {'url': 'es/la-liga-2'},
    "Ligue 1":  {'url': 'fr/ligue-1'},
    "Ligue 2":  {'url': 'fr/ligue-2'},
    "Eredivisie":  {'url': 'ne/eredivisie'},
    "Primeira Liga":  {'url': 'pt/primeira-liga'},
    "Scottish PL":  {'url': 'uk/scottish-premiership'},
    "Super Lig":  {'url': 'tr/super-lig'},
    "Belgian 1st Division":  {'url': 'be/first-division-a'},
}


class Capology():

    # ==============================================================================================
    def __init__(self) -> None:
        self.valid_currencies = ['eur', 'gbp', 'usd']

    # ==============================================================================================
    def _webdriver_init(self) -> None:
        """ Initializes a new webdriver
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--incognito')
        prefs = {'profile.managed_default_content_settings.images': 2}  # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options)

    # ==============================================================================================
    def _webdriver_close(self) -> None:
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

    # ==============================================================================================
    def get_league_url(self, league: str) -> str:
        """ Returns the URL for the requested league

        Parameters
        ----------
        league : str
            League to be scraped (e.g., "EPL"). See the comps variable in ScraperFC.Capology for
            valid leagues for this module.
        Returns
        -------
        : str
            League URL
        """
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Capology', list(comps.keys()))

        return f'https://www.capology.com/{comps[league]["url"]}/salaries/'

    # ==============================================================================================
    def get_valid_seasons(self, league: str) -> Sequence[str]:
        """ Returns valid season strings for the chosen league

        Parameters
        ----------
        league : str
            League to be scraped (e.g., "EPL"). See the comps variable in ScraperFC.Capology for
            valid leagues for this module.
        Returns
        -------
        : list of str
            List of valid year strings for this league
        """
        if not isinstance(league, str):
            raise TypeError('`league` must be a string.')
        if league not in comps.keys():
            raise InvalidLeagueException(league, 'Capology', list(comps.keys()))

        soup = BeautifulSoup(requests.get(self.get_league_url(league)).content, 'html.parser')
        year_dropdown_tags = soup.find('select', {'id': 'nav-submenu2'})\
            .find_all('option', value=True)  # type: ignore
        seasons = [x.text for x in year_dropdown_tags]

        return seasons

    # ==============================================================================================
    def get_season_url(self, year: str, league: str) -> str:
        """ Gets URL to chosen year of league

        Parameters
        ----------
        year : str
            See the :ref:`capology_year` `year` parameter docs for details.
        league : str
            League to be scraped (e.g., "EPL"). See the comps variable in ScraperFC.Capology for
            valid leagues for this module.
        Returns
        -------
        : str
            Season URL
        """
        if not isinstance(year, str):
            raise TypeError('`year` must be a string.')
        valid_seasons = self.get_valid_seasons(league)
        if year not in valid_seasons:
            raise InvalidYearException(year, league, valid_seasons)
        
        soup = BeautifulSoup(requests.get(self.get_league_url(league)).content, 'html.parser')
        year_dropdown_tags = soup.find('select', {'id': 'nav-submenu2'})\
            .find_all('option', value=True)  # type: ignore
        value = [x['value'] for x in year_dropdown_tags if x.text == year][0]

        return f'https://capology.com{value}'

    # ==============================================================================================
    def scrape_salaries(self, year: str, league: str, currency: str) -> pd.DataFrame:
        """ Scrapes player salaries for the given league season.

        Parameters
        ----------
        year : str
            See the :ref:`capology_year` `year` parameter docs for details.
        league : str
            League to be scraped (e.g., "EPL"). See the comps variable in ScraperFC.Capology for
            valid leagues for this module.
        currency : str
            The currency for the returned salaries. Options are "eur" for Euro, "gbp" for British
            Pound, and "USD" for US Dollar
        Returns
        -------
        : DataFrame
            The salaries of all players in the given league season
        """
        if not isinstance(currency, str):
            raise TypeError('`currency` must be a string.')
        if currency not in self.valid_currencies:
            raise InvalidCurrencyException()

        self._webdriver_init()
        try:
            self.driver.get(self.get_season_url(year, league))

            # Show all players on one page ---------------------------------------------------------
            done = False
            while not done:
                try:
                    all_btn = WebDriverWait(self.driver, 10)\
                        .until(EC.element_to_be_clickable((By.LINK_TEXT, 'All')))
                    self.driver.execute_script('arguments[0].click()', all_btn)
                    done = True
                except StaleElementReferenceException:
                    pass

            # Select the currency ------------------------------------------------------------------
            currency_btn = WebDriverWait(self.driver, 10)\
                .until(EC.element_to_be_clickable((By.ID, f'btn_{currency}')))
            self.driver.execute_script('arguments[0].click()', currency_btn)
            print('Changed currency')

            # Table to pandas df -------------------------------------------------------------------
            tbody_html = self.driver.find_element(By.ID, 'table')\
                .find_element(By.TAG_NAME, 'tbody').get_attribute('outerHTML')
            table_html = '<table>' + tbody_html + '</table>'  # type: ignore
            df = pd.read_html(StringIO(table_html))[0]
            if df.shape[1] == 13:
                # drop check-mark column
                df = df.drop(columns=[1])
                df.columns = [
                    'Player', 'Weekly Gross', 'Annual Gross', 'Expiration', 'Length', 'Total Gross',
                    'Status', 'Pos. group', 'Pos.', 'Age', 'Country', 'Club'
                ]  # type: ignore
            elif df.shape[1] == 17:
                # drop check-mark column and True/False column (not sure what this one is)
                df = df.drop(columns=[1, 16])
                df.columns = [
                    'Player', 'Weekly Gross', 'Annual Gross', 'Annual Bonus', 'Signed',
                    'Expiration', 'Years Reamining', 'Gross Remaining', 'Release Clause', 'Status',
                    'Pos. group', 'Pos.', 'Age', 'Country', 'Club'
                ]  # type: ignore
            else:
                df.columns = [
                    'Player', 'Weekly Gross', 'Annual Gross', 'Adj. Gross', 'Pos. group', 'Age',
                    'Country', 'Club'
                ]  # type: ignore

            return df
        finally:
            self._webdriver_close()

    # ==============================================================================================
    def scrape_payrolls(self, year: str, league: str, currency: str) -> pd.DataFrame:
        """ Deprecated. Use scrape_salaries() instead.
        """
        raise NotImplementedError(
            '`scrape_payrolls()` has been deprecated. Please use `scrape_salaries()` instead.'
        )
        # """ Scrapes team payrolls for the given league season.

        # Parameters
        # ----------
        # year : str
        #     Season to be scraped (e.g, "2020-21"). Please use the same string that is in the
        #     season dropdown on the Capology website. Call
        #     ScraperFC.Capology.get_valid_seasons(league) to see valid seasons for a league.
        # league : str
        #     League to be scraped (e.g., "EPL"). See the comps variable in ScraperFC.Capology for
        #     valid leagues for this module.
        # currency : str
        #     The currency for the returned salaries. Options are "eur" for Euro, "gbp" for British
        #     Pound, and "USD" for US Dollar
        # Returns
        # -------
        # : Pandas DataFrame
        #     The payrolls of all teams in the given league season
        # """
        # if type(currency) is not str:
        #     raise TypeError('`currency` must be a string.')
        # if currency not in self.valid_currencies:
        #     raise InvalidCurrencyException()

        # self._webdriver_init()
        # try:
        #     self.driver.get(self.get_season_url(year, league))

        #     # select the currency
        #     currency_btn = (
        #         WebDriverWait(self.driver, 10)
        #         .until(EC.element_to_be_clickable((By.ID, f'btn_{currency}')))
        #     )
        #     self.driver.execute_script('arguments[0].click()', currency_btn)

        #     # table to pandas df
        #     table = (
        #         WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'table')))
        #     )
        #     df = pd.read_html(StringIO(table.get_attribute('outerHTML')))[0]
        #     # df.columns = [
        #     #     'Club', 'Weekly Gross (000s)', 'Annual Gross (000s)',
        #     #     'Inflcation-Adj. Gross (000s)', 'Keeper (000s)', 'Defense (000s)',
        #     #     'Midfield (000s)', 'Forward (000s)'
        #     # ]

        #     return df
        # finally:
        #     self._webdriver_close()

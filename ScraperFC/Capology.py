from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
from IPython.display import clear_output

from ScraperFC.shared_functions import get_source_comp_info, InvalidCurrencyException

class Capology():

    ############################################################################
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options)

        self.leagues = {
            'Bundesliga': 'de/1-bundesliga',
            '2.Bundesliga': '/de/2-bundesliga',
            'EPL': 'uk/premier-league',
            'EFL Championship': '/uk/championship',
            'Serie A': 'it/serie-a',
            'Serie B': 'it/serie-b',
            'La Liga': 'es/la-liga',
            'La Liga 2': 'es/la-liga-2',
            'Ligue 1': 'fr/ligue-1',
            'Ligue 2': 'fr/ligue-2',
            'Eredivisie': '/ne/eredivisie',
            'Primeira Liga': '/pt/primeira-liga',
            'Scottish PL': '/uk/scottish-premiership',
            'Super Lig': '/tr/super-lig',
            'Belgian 1st Division': 'be/first-division-a'
        }

        self.valid_currencies = ['eur', 'gbp', 'usd']


    ############################################################################
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

    
    ############################################################################
    def scrape_salaries(self, year, league, currency):
        """ Scrapes player salaries for the given league season.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        currency : str
            The currency for the returned salaries. Options are "eur" for Euro,\
            "gbp" for British Pount, and "USD" for US Dollar
        Returns
        -------
        : Pandas DataFrame
            The salaries of all players in the given league season
        """
        _ = get_source_comp_info(year, league, 'Capology')
        if currency not in self.valid_currencies:
            raise InvalidCurrencyException()

        league_url = f'https://www.capology.com/{self.leagues[league]}/salaries/{year-1}-{year}'
        self.driver.get(league_url)

        # Show all players on one page -----------------------------------------
        done = False
        while not done:
            try:
                all_btn = WebDriverWait(
                    self.driver, 
                    10,
                ).until(EC.element_to_be_clickable(
                    (By.LINK_TEXT, 'All')
                ))
                all_btn.click()
                done = True
            except StaleElementReferenceException:
                pass

        # Select the currency --------------------------------------------------
        currency_btn = WebDriverWait(
            self.driver, 
            10,
        ).until(EC.element_to_be_clickable(
            (By.ID, 'btn_{}'.format(currency))
        ))
        self.driver.execute_script('arguments[0].click()', currency_btn)
        print('Changed currency')

        # Table to pandas df ---------------------------------------------------
        tbody_html = self.driver.find_element(By.ID, 'table')\
                .find_element(By.TAG_NAME, 'tbody')\
                .get_attribute('outerHTML')
        table_html = '<table>' + tbody_html + '</table>'
        df = pd.read_html(table_html)[0]
        if df.shape[1] == 13:
            df = df.drop(columns=[1])
            df.columns = [
                'Player', 'Weekly Gross', 'Annual Gross', 'Expiration', 'Length', 
                'Total Gross', 'Status', 'Pos. group', 'Pos.', 'Age', 'Country', 
                'Club'
            ]
        else:
            df.columns = [
                'Player', 'Weekly Gross', 'Annual Gross', 'Adj. Gross', 'Pos. group', 
                'Age', 'Country', 'Club'
            ]

        return df

    
    ############################################################################
    def scrape_payrolls(self, year, league, currency):
        """ Scrapes team payrolls for the given league season.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        currency : str
            The currency for the returned salaries. Options are "eur" for Euro,\
            "gbp" for British Pount, and "USD" for US Dollar
        Returns
        -------
        : Pandas DataFrame
            The payrolls of all teams in the given league season
        """
        _ = get_source_comp_info(year, league, 'Capology')
        if currency not in self.valid_currencies:
            raise InvalidCurrencyException()

        
        league_url = 'https://www.capology.com/{}/payrolls/{}-{}'.format(self.leagues[league], year-1, year)

        self.driver.get(league_url)

        # select the currency
        currency_btn = WebDriverWait(
            self.driver, 
            10,
        ).until(EC.element_to_be_clickable(
            (By.ID, 'btn_{}'.format(currency))
        ))
        self.driver.execute_script('arguments[0].click()', currency_btn)

        # table to pandas df
        table = WebDriverWait(
            self.driver, 
            10,
        ).until(EC.element_to_be_clickable(
            (By.ID, 'table')
        ))
        done = False
        while not done:
            df = pd.read_html(table.get_attribute('outerHTML'))[0]
            done = True if df.shape[0]>0 else False
        # df.columns = [
        #     'Club', 'Weekly Gross (000s)', 'Annual Gross (000s)', 'Inflcation-Adj. Gross (000s)',
        #     'Keeper (000s)', 'Defense (000s)', 'Midfield (000s)', 'Forward (000s)'
        # ]

        return df

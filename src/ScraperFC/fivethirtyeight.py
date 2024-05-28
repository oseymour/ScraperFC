from .shared_functions import xpath_soup
from .scraperfc_exceptions import InvalidLeagueException, InvalidYearException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pandas as pd
from zipfile import ZipFile
import time
from bs4 import BeautifulSoup


class FiveThirtyEight:
    
    # ==============================================================================================
    def __init__(self):
        return

    # ==============================================================================================
    def _webdriver_init(self):
        """ Private, creates a selenium webdriver instance
        """
        options = Options()
        options.add_argument('--headless')
        prefs = {'download.default_directory': os.getcwd()}
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options)
        
    # ==============================================================================================    
    def _webdriver_close(self):
        """ Private, closes the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()
        
    # ==============================================================================================  
    def scrape_matches(self, year, league):
        """ Scrapes matches for the given league season

        Parameters
        ----------
        year : int
            Calendar year that the season begins in (e.g. 2022 for the 2022/23 season). This is 
            different from FiveThirtyEight versus other ScraperFC modules.
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        Returns
        -------
        : DataFrame
        """
        if type(year) is not int and year != 'All':
            raise TypeError('`year` must be an int.')
        if type(league) is not str:
            raise TypeError('`league` must be a string.')
        
        self._webdriver_init()

        try:
            # Load URL
            self.driver.get('https://data.fivethirtyeight.com/#soccer-spi')
            
            # Wait for data index to be available
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'dataIndex')))

            # Click download button
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            button_xpath = xpath_soup(soup.find('div', {'dataset-name': 'soccer-spi'}))
            button = self.driver.find_element(By.XPATH, button_xpath)
            self.driver.execute_script('arguments[0].click();', button)
                    
            # Wait for download to complete
            while not os.path.exists('soccer-spi.zip'):
                time.sleep(1)
            
            # Get data table
            with ZipFile('soccer-spi.zip') as zf:
                with zf.open('soccer-spi/spi_matches.csv') as f:
                    df = pd.read_csv(f)
                    
            # Delete downloaded folder
            os.remove('soccer-spi.zip')
        
            # Pick the chosen league or keep all
            if league == 'All':
                pass
            elif league not in df['league'].values:
                raise InvalidLeagueException(
                    league, 'FiveThirtyEight', list(set((df['league'].values)))
                )
            else:
                df = df[df['league'] == league]

            # Get the requested year or keep all
            if year == 'All':
                pass
            elif year not in df['season'].values:
                raise InvalidYearException(year, league, list(set(df['season'].values)))
            else:
                df = df[df['season'] == year].reset_index(drop=True)

            return df
        finally:
            self._webdriver_close()

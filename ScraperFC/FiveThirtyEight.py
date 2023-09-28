from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pandas as pd
import numpy as np
from IPython.display import clear_output
from zipfile import ZipFile
from ScraperFC.shared_functions import get_source_comp_info, xpath_soup
import time
from bs4 import BeautifulSoup

class FiveThirtyEight:
    
    ############################################################################
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        prefs = {"download.default_directory" : os.getcwd()}
        options.add_experimental_option("prefs",prefs)
        self.driver = webdriver.Chrome(options=options)
        
    ############################################################################    
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()
        
    ############################################################################    
    def up_season(self, string):
        """ Increments a string of the season year
        
        Args
        ----
        string : str
            String of a calendar year (e.g. "2022")
        Returns
        -------
        : str
            Incremented calendar year
        """
        return str(int(string) + 1)
        
    ############################################################################  
    def scrape_matches(self, year, league, save=False):
        """ Scrapes matches for the given league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        save : bool
            OPTIONAL, default is False. If True, output will be saved to a CSV file.
        Returns
        -------
        : Pandas DataFrame
            If save=False, FiveThirtyEight stats for all matches of the given\
            league season
        filename : str
            If save=True, filename of the CSV that the stats were saved to 
        """
        _ = get_source_comp_info(year,league,'FiveThirtyEight')
        
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
        
        # Pick the chosen league
        if league == "EPL":
            df = df[df['league'] == 'Barclays Premier League']
        elif league == "La Liga":
            df = df[df['league'] == 'Spanish Primera Division']
        elif league == "Bundesliga":
            df = df[df['league'] == 'German Bundesliga']
        elif league == "Serie A":
            df = df[df['league'] == 'Italy Serie A']
        elif league == "Ligue 1":
            df = df[df['league'] == 'French Ligue 1']
        
        # Add one to season column
        df['season'] = df['season'].apply(self.up_season)
        
        # Only keep the season requested
        df = df[df['season']==str(year)].reset_index(drop=True)
        
        # Save to CSV if requested by user
        if save:
            filename = f'{year}_{league}_FiveThirtyEight_matches.csv'
            df.to_csv(path_or_buf=filename, index=False)
            print('Matches dataframe saved to ' + filename)
            return filename
        else:
            return df
        
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from ScraperFC.shared_functions import *
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time


class Transfermarkt():
    
    ############################################################################
    def __init__(self):
        options = Options()
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options)

        # Deal with Accept All popup
        self.driver.get('https://www.transfermarkt.us')
        # Switch to the iframe popup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        iframe = self.driver.find_element(
            By.XPATH, 
            xpath_soup(soup.find('div', {'id': re.compile('sp_message_container')}).find('iframe'))
        )
        self.driver.switch_to.frame(iframe)
        # Press the ACCEPT ALL button
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        accept_all_button = self.driver.find_element(
            By.XPATH,
            xpath_soup(soup.find('button', {'aria-label': 'ACCEPT ALL'}))
        )
        self.driver.execute_script('arguments[0].click()', accept_all_button)
        # Switch back to the main window
        self.driver.switch_to.default_content()
        # Wait until popup is gone from HTML
        gone = False
        while not gone:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            popup_matches = soup.find_all('div', {'id': re.compile('sp_message_container')})
            gone = True if len(popup_matches)==0 else False
            time.sleep(1) # wait for a hot sec

        
    ############################################################################
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

        
    ############################################################################
    def get_club_links(self, year, league):
        """ Gathers all Transfermarkt club URL's for the chosen league season.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        Returns
        -------
        : list
            List of the club URL's
        """
        _ = get_source_comp_info(year, league, 'Transfermarkt')
        
        competition_links = {
            'EPL': 'https://www.transfermarkt.us/premier-league/startseite/wettbewerb/GB1',
            'EFL Championship': 'https://www.transfermarkt.us/championship/startseite/wettbewerb/GB2',
            'EFL1': 'https://www.transfermarkt.us/league-one/startseite/wettbewerb/GB3',
            'EFL2': 'https://www.transfermarkt.us/league-two/startseite/wettbewerb/GB4',
            'Bundesliga': 'https://www.transfermarkt.us/bundesliga/startseite/wettbewerb/L1',
            '2.Bundesliga': 'https://www.transfermarkt.us/2-bundesliga/startseite/wettbewerb/L2',
            'Serie A': 'https://www.transfermarkt.us/serie-a/startseite/wettbewerb/IT1',
            'Serie B': 'https://www.transfermarkt.us/serie-b/startseite/wettbewerb/IT2',
            'La Liga': 'https://www.transfermarkt.us/laliga/startseite/wettbewerb/ES1',
            'La Liga 2': 'https://www.transfermarkt.us/laliga2/startseite/wettbewerb/ES2',
            'Ligue 1': 'https://www.transfermarkt.us/ligue-1/startseite/wettbewerb/FR1',
            'Ligue 2': 'https://www.transfermarkt.us/ligue-2/startseite/wettbewerb/FR2',
            'Eredivisie': 'https://www.transfermarkt.us/eredivisie/startseite/wettbewerb/NL1',
            'Scottish PL': 'https://www.transfermarkt.us/scottish-premiership/startseite/wettbewerb/SC1',
            'Super Lig': 'https://www.transfermarkt.us/super-lig/startseite/wettbewerb/TR1',
            'Jupiler Pro League': 'https://www.transfermarkt.us/jupiler-pro-league/startseite/wettbewerb/BE1',
            'Liga Nos': 'https://www.transfermarkt.us/liga-nos/startseite/wettbewerb/PO1',
            'Russian Premier League': 'https://www.transfermarkt.us/premier-liga/startseite/wettbewerb/RU1',
            'Brasileirao': 'https://www.transfermarkt.us/campeonato-brasileiro-serie-a/startseite/wettbewerb/BRA1',
            'Argentina Liga Profesional': 'https://www.transfermarkt.us/superliga/startseite/wettbewerb/AR1N',
            'MLS': 'https://www.transfermarkt.us/major-league-soccer/startseite/wettbewerb/MLS1'
        }
        
        # Go to the selected year
        url = '{}/plus/?saison_id={}'.format(competition_links[league], year-1)
        self.driver.get(url)
        
        # Get the club links
        club_links = set()
        table = self.driver.find_elements(By.CLASS_NAME, 'items')[0]
        for el in table.find_elements(By.TAG_NAME, 'td'):
            if 'hauptlink no-border-links' in el.get_attribute('class'):
                href = el.find_element(By.TAG_NAME, 'a').get_attribute('href')
                club_links.add(href)
            
        return list(club_links)
    
    
    ############################################################################
    def get_player_links(self, year, league):
        """ Gathers all Transfermarkt player URL's for the chosen league season.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        Returns
        -------
        : list
            List of the player URL's
        """
        _ = get_source_comp_info(year, league, 'Transfermarkt')
        
        player_links = set()
        club_links = self.get_club_links(year, league)
        for club_link in tqdm(club_links, desc='Gathering player links'):
            self.driver.get(club_link)
            
            # Get players from the table on the club page
            table = self.driver.find_elements(By.CLASS_NAME, 'items')[0]
            for el in table.find_elements(By.CLASS_NAME, 'hauptlink'):
                try:
                    subel = WebDriverWait(el, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'a')))
                except TimeoutException:
                    # Ben White f*cked everything up. For some reason, this works
                    continue
                href = subel.get_attribute('href')
                if 'profil' in href:
                    player_links.add(href)
                
        return list(player_links)
    
    ############################################################################
    def get_players(self, year, league):
        """ Gathers all player info for the chosen league season.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        Returns
        -------
        : Pandas DataFrame
            Each row is a player and contains some of the information from their\
            Transfermarkt player profile.
        """
        _ = get_source_comp_info(year, league, 'Transfermarkt')
        
        player_links = self.get_player_links(year, league)
        df = pd.DataFrame()
        iter = tqdm(player_links)
        for player_link in iter:
            iter.set_description(f'Scraping player {player_link}')
            player = TransfermarktPlayer(player_link)
            new_row = pd.Series(dtype=object)
            new_row["Name"] = player.name
            new_row["Value"] = player.value
            new_row["Value last updated"] = player.value_last_updated
            new_row["DOB"] = player.dob
            new_row["Age"] = player.age
            new_row["Height (m)"] = player.height_meters
            new_row["Nationality"] = player.nationality
            new_row["Citizenship"] = player.citizenship
            new_row["Position"] = player.position
            if player.other_positions is None:
                new_row["Other positions"] = None
            else:
                new_row["Other positions"] = pd.DataFrame(player.other_positions)
            new_row["Team"] = player.team
            new_row["Joined"] = player.joined
            new_row["Contract expires"] = player.contract_expires
            new_row["Market value history"] = player.market_value_history
            new_row["Transfer history"] = player.transfer_history
            df = pd.concat([df, new_row.to_frame().T], axis=0, ignore_index=True)
        return df
    

################################################################################
class TransfermarktPlayer():
    """ Class to represent Transfermarkt player profiles.
    
    Initialize with the URL to a player's Transfermarkt profile page.
    """
    
    def __init__(self, url):
        self.url = url
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '+\
                'AppleWebKit/537.36 (KHTML, like Gecko) '+\
                'Chrome/55.0.2883.87 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Name
        data_header_el = soup.find("h1", {"class": "data-header__headline-wrapper"})
        self.name = data_header_el.getText().split('\n')[-1].strip()
        
        # Value
        try:
            self.value = soup.find("a", {"class": "data-header__market-value-wrapper"}).text.split(" ")[0]
            self.value_last_updated = soup.find("a", {"class": "data-header__market-value-wrapper"}).text.split("Last update: ")[-1]
        except AttributeError:
            self.value = None
            self.value_last_updated = None
            
        # DOB and age
        dob_el = soup.find("span", {"itemprop": "birthDate"})
        self.dob = ' '.join(dob_el.getText().strip().split(' ')[:3])
        self.age = int(dob_el.getText().strip().split(' ')[-1].replace('(','').replace(')',''))
        
        # Height
        height_el = soup.find("span", {"itemprop": "height"})
        try:
            self.height_meters = float(height_el.getText().replace("m", "").replace(",", "."))
        except AttributeError:
            self.height_meters = None
       
        # Citizenship
        nationality_el = soup.find("span", {"itemprop": "nationality"})
        self.nationality = nationality_el.getText().replace("\n","").strip()
        citizenship_els = soup.find_all("span", {"class": "info-table__content info-table__content--bold"})
        flag_els = [flag_el for el in citizenship_els\
            for flag_el in el.find_all("img", {"class": "flaggenrahmen"})]
        self.citizenship = list(set([el["title"] for el in flag_els]))
        
        # Position
        position_el = soup.find("dd", {"class": "detail-position__position"})
        if position_el is None:
            position_el = [el for el in soup.find_all('li', {'class': 'data-header__label'}) if 'position' in el.text.lower()][0].find('span')
        self.position = position_el.text.strip()
        try:
            self.other_positions = [el.getText() for el in soup.find("div", {"class": "detail-position__position"}).find_all("dd")]
        except AttributeError:
            self.other_positions = None
        
        # Team & Contract
        try:
            self.team = soup.find("span", {"class": "data-header__club"}).find("a")["title"]
        except TypeError:
            self.team = "Retired"
        if self.team in ["Without Club", "Retired"]:
            self.joined = None
            self.contract_expires = None
        else:
            self.joined = [el.text.split(": ")[-1] \
                for el in soup.find_all("span", {"class": "data-header__label"}) \
                if "joined" in el.text.lower()][0]
            self.contract_expires = [el.text.split(": ")[-1] \
                for el in soup.find_all("span", {"class": "data-header__label"}) \
                if "expires" in el.text.lower()][0]
        
        # Market value history
        try:
            script = [s for s in soup.find_all("script", {"type": "text/javascript"}) \
                      if "var chart = new Highcharts.Chart" in str(s)][0]
            values = [int(s.split(",")[0]) for s in str(script).split("y':")[2:-2]]
            dates = [s.split("datum_mw':")[-1].split(",'x")[0].replace("\\x20"," ").replace("'", "") \
                     for s in str(script).split("y':")[2:-2]]
            self.market_value_history = pd.DataFrame({"date": dates, "value": values})
        except IndexError:
            self.market_value_history = None
        
        # Transfer History
        rows = soup.find_all("div", {"class": "grid tm-player-transfer-history-grid"})
        self.transfer_history = pd.DataFrame(
            data=[[s.strip() for s in row.getText().split("\n\n") if s!=""] for row in rows],
            columns=['Season', 'Date', 'Left', 'Joined', 'MV', 'Fee', '']
        ).drop(
            columns=['']
        )
        
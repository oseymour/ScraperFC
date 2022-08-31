from IPython.display import clear_output
import numpy as np
import pandas as pd
from ScraperFC.shared_functions import check_season
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
# from lxml import etree
from tqdm import tqdm
import time
import re
from datetime import datetime


class FBRef:
    """ ScraperFC module for FBRef
    """
    
    ################################################################################
    def __init__(self): #, driver='chrome'):
        # assert driver in ['chrome', 'firefox']
 
        self.wait_time = 5

        #if driver == 'chrome':
        from selenium.webdriver.chrome.service import Service as ChromeService
        options = Options()
        options.headless = True
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'+\
            ' (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        )
        options.add_argument('window-size=1400,600')
        options.add_argument('--incognito')
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        options.add_argument('--log-level=3')
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
#         elif driver == 'firefox':
#             from selenium.webdriver.chrome.service import Service as FirefoxService
#             self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
      
    ################################################################################    
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

    ################################################################################
    def get(self, url):
        """ Custom get function just for the FBRef module. 
        
        Calls .get() from the Selenium WebDriver and then waits in order to avoid\
        a Too Many Requests HTTPError from FBRef. 
        
        Args
        ----
        url : str
            The URL to get
        Returns
        -------
        None
        """
        self.driver.get(url)
        time.sleep(self.wait_time)
        
    ############################################################################
    def requests_get(self, url):
        """ Custom requests.get function for the FBRef module
        
        Calls requests.get() until the status code is 200.

        Args
        ----
        url : Str
            The URL to get
        Returns
        -------
        None
        """
        got_link = False # Don't proceed until we've successfully retrieved the page
        while not got_link:
            response = requests.get(url)
            time.sleep(5)
            if response.status_code == 200:
                # 200 - OK
                # 403 - file not found
                # 500 - server error
                got_link = True
        return response
        

    ################################################################################
    def get_season_link(self, year, league):
        """ Returns the URL for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        Returns
        -------
        : str
            URL to the FBRef page of the chosen league season 
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        
        # urls are to league's seasons history page
        # finders are used later to make sure we're getting the right season URL
        urls_finders = {
            'EPL': {
                'url': 'https://fbref.com/en/comps/9/history/Premier-League-Seasons',
                'finder': 'Premier-League-Stats'
            },
            'La Liga': {
                'url': 'https://fbref.com/en/comps/12/history/La-Liga-Seasons',
                'finder': 'La-Liga-Stats'
            },
            'Bundesliga': {
                'url': 'https://fbref.com/en/comps/20/history/Bundesliga-Seasons',
                'finder': 'Bundesliga-Stats'
            },
            'Serie A': {
                'url': 'https://fbref.com/en/comps/11/history/Serie-A-Seasons',
                'finder': 'Serie-A-Stats'
            },
            'Ligue 1': {
                'url': 'https://fbref.com/en/comps/13/history/Ligue-1-Seasons',
                'finder': 'Ligue-1-Stats' if year>=2003 else 'Division-1-Stats'
            },
            'MLS': {
                'url': 'https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons',
                'finder': 'Major-League-Soccer-Stats'
            },
        }
        url = urls_finders[league]['url']
        finder = urls_finders[league]['finder']
        
        # self.driver.get(url) # go to league's seasons page
        self.get(url)
        
        # Generate season string to find right element
        if league != 'MLS':
            season = str(year-1)+'-'+str(year)
        else:
            season = str(year)
           
        # Get url to season
        for el in self.driver.find_elements(By.LINK_TEXT, season):
            if finder in el.get_attribute('href'):
                return el.get_attribute('href')
            else:
                print('ERROR: Season not found.')
                return -1
    
    ################################################################################
    def get_match_links(self, year, league):
        """ Gets all match links for the chosen league season.

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
            FBRef links to all matches for the chosen league season
        """
        print('Gathering match links.')
        url = self.get_season_link(year, league)
        
        # go to the scores and fixtures page
        url = url.split('/')
        first_half = '/'.join(url[:-1])
        second_half = url[-1].split('-')
        second_half = '-'.join(second_half[:-1])+'-Score-and-Fixtures'
        url = first_half+'/schedule/'+second_half
        # self.driver.get(url)
        self.get(url)
        
        # Get links to all of the matches in that season
        finders = {'EPL': '-Premier-League',
                   'La Liga': '-La-Liga',
                   'Bundesliga': '-Bundesliga',
                   'Serie A': '-Serie-A',
                   'Ligue 1': '-Ligue-1' if year>=2003 else '-Division-1',
                   'MLS': '-Major-League-Soccer'}
        finder = finders[league]
        
        links = set()
        # only get match links from the fixtures table
        for table in self.driver.find_elements(By.TAG_NAME, 'table'):
            if table.get_attribute('id')!='' and table.get_attribute('class')!='':
                # find the match links
                for element in tqdm(table.find_elements(By.TAG_NAME, 'a')):
                    href = element.get_attribute('href')
                    if (href) and ('/matches/' in href) and (href.endswith(finder)):
                        links.add(href)
        
        return list(links)
    
    ################################################################################
    def add_team_ids(self, df, insert_index, season_url, tag_name):
        """ Add team ID's to a dataframe

        Args
        ----
        df : Pandas DataFrame
            Dataframe of team stats
        insert_index : int
            Column index to insert the ID's into
        season_url : str
            FBRef URL to a league season
        tag_name :str
            HTML tag name to use for team ID search
        Returns
        ------- 
        : Pandas DataFrame
            The dataframe passed in as an arg, with the team ID's added as a new column
        """
        # self.driver.get(season_url)
        self.get(season_url)
        team_ids = list()
        for el in self.driver.find_elements(By.XPATH, f'//{tag_name}[@data-stat="team"]'):
            if el.text != '' and el.text != 'Squad':
                team_id = el.find_element(By.TAG_NAME, 'a') \
                            .get_attribute('href') \
                            .split('/squads/')[-1] \
                            .split('/')[0]
                team_ids.append(team_id)
        df.insert(insert_index, 'team_id', team_ids)
        return df

    ################################################################################
    def add_player_ids_and_links(self, df, url):
        """ Add player ID's and FBRef URL's to a dataframe
        
        Args
        ----
        df : Pandas DataFrame
            Dataframe of player stats
        url : str
            FBRef URL to the player stats page being scraped to generate df
        Returns
        ------
        : Pandas DataFrame
            The dataframe passed as an arg, but with new columns with player ID's and\
            player URL's
        """
        # self.driver.get(url)
        self.get(url)
        player_ids = list()
        player_links = list()
        for el in self.driver.find_elements(By.XPATH, '//td[@data-stat="player"]'):
            if el.text != '' and el.text != 'Player':
                player_id = el.find_element(By.TAG_NAME, 'a') \
                    .get_attribute('href') \
                    .split('/players/')[-1] \
                    .split('/')[0]
                player_ids.append(player_id)
                player_links.append(el.find_element(By.TAG_NAME, 'a').get_attribute('href'))
        df.insert(2, 'player_id', player_ids) # insert player IDs as new col in df
        df.insert(2, 'player_link', player_links) # insert player links as new col in df
        return df
    
    ################################################################################
    def normalize_table(self, xpath):
        """ Written to the press the "Toggle Per90 Stats" button on FBRef pages.\
            Should be able to be used to press any button, however.
        
        Args
        ----
        xpath : str
            XPath to the button to be pressed. This will be unique for each page\
            being scraped.
        Returns
        ------- 
        None
        """
        button = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script('arguments[0].click()',button)
    
    ################################################################################
    def get_html_w_id(self, ID):
        """ Returns the HTML of a Selenium WebElement based on a search of the \
            element ID field
        
        Args
        ----
        ID : str
            Element ID to use for search
        Returns
        -------
        : str
            HTML of the first WebElement matching the passed ID
        """
        return self.driver.find_element(By.ID, ID).get_attribute('outerHTML')

    ################################################################################
    def scrape_league_table(self, year, league, normalize=False):
        """ Scrapes the league table of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped league table.
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        print('Scraping {} {} league table'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        df = pd.read_html(url)
        lg_tbl = df[0].copy()
        #### Drop columns and normalize
        if year >= 2018:
            lg_tbl.drop(columns=['xGD/90'], inplace=True)
        if normalize and year >= 2018:
            lg_tbl.iloc[:,3:13] = lg_tbl.iloc[:,3:13].divide(lg_tbl['MP'], axis='rows')
        elif normalize and year < 2018:
            lg_tbl.iloc[:,3:10] = lg_tbl.iloc[:,3:10].divide(lg_tbl['MP'], axis='rows')
        #### Scrape western conference if MLS
        if league == 'MLS':
            west_tbl = df[2].copy()
            if year >= 2018:
                west_tbl.drop(columns=['xGD/90'], inplace=True)
            if normalize and year >= 2018:
                west_tbl.iloc[:,3:13] = west_tbl.iloc[:,3:13].divide(west_tbl['MP'], axis='rows')
            elif normalize and year < 2018:
                west_tbl.iloc[:,3:10] = west_tbl.iloc[:,3:10].divide(west_tbl['MP'], axis='rows')
            return (lg_tbl, west_tbl)
        lg_tbl = self.add_team_ids(lg_tbl, 2, url, 'td') # Get team IDs
        return lg_tbl
    
    ################################################################################
    def scrape_standard(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef standard stats page of the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        print('Scraping {} {} standard stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/stats/' + new[-1]
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_standard_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_standard')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(columns='Per 90 Minutes', level=0, inplace=True)
            df.drop(columns='Matches', level=1, inplace=True)
            # convert some column types from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            # add some calculated columns
            df[('Performance','G+A')] = df[('Performance','Gls')] + df[('Performance','Ast')]
            df[('Performance','G+A-PK')] = df[('Performance','G+A')] - df[('Performance','PK')]
            if year >= 2018:
                df[('Expected','xG+xA')] = df[('Expected','xG')] + df[('Expected','xA')]
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            drop_cols = squad.xs('Per 90 Minutes', axis=1, level=0, drop_level=False).columns
            squad.drop(columns=drop_cols, inplace=True)
            vs.drop(columns=drop_cols, inplace=True)
            if normalize:
                squad.iloc[:,8:] = squad.iloc[:,8:].divide(squad[('Playing Time','90s')], axis='rows')
                vs.iloc[:,8:] = vs.iloc[:,8:].divide(vs[('Playing Time','90s')], axis='rows')
            col = ('Performance','G+A')
            squad[col] = squad[('Performance','Gls')] + squad[('Performance','Ast')]
            vs[col] = vs[('Performance','Gls')] + vs[('Performance','Ast')]
            col = ('Performance','G+A-PK')
            squad[col] = squad[('Performance','G+A')] - squad[('Performance','PK')]
            vs[col] = vs[('Performance','G+A')] - vs[('Performance','PK')]
            if year >= 2018:
                col = ('Expected','xG+xA')
                squad[col] = squad[('Expected','xG')] + squad[('Expected','xA')]
                vs[col] = vs[('Expected','xG')] + vs[('Expected','xA')]
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_gk(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef goalkeeper stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif league in['La Liga','Bundesliga','Ligue 1'] and year<2000:
            print('Goalkeeping stats not available from',league,'before 1999/2000 season.')
            return -1
        elif league=='Serie A' and year<1999:
            print('Goalkeeping stats not available from Serie A before 1998/99 season.')
            return -1
        print('Scraping {} {} goalkeeping stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/keepers/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_keeper_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_keeper')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(columns=('Performance','GA90'), inplace=True)
            df.drop(columns='Matches', level=1, inplace=True)
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            squad.drop(columns=('Performance','GA90'), inplace=True)
            vs.drop(columns=('Performance','GA90'), inplace=True)
            if normalize:
                keep_cols = [('Performance','Save%'), ('Performance','CS%'), ('Penalty Kicks','Save%')]
                keep = squad[keep_cols]
                squad.iloc[:,6:] = squad.iloc[:,6:].divide(squad[('Playing Time','90s')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,6:] = vs.iloc[:,6:].divide(vs[('Playing Time','90s')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_adv_gk(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef advanced goalkeeper stats page of the chosen league \
            season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif year < 2018:
            print('Advanced goalkeeping stats not available from before the 2017/18 season.')
            return -1
        print('Scraping {} {} advanced goalkeeping stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/keepersadv/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_keeper_adv_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_keeper_adv')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(columns=['Matches', '#OPA/90', '/90'], level=1, inplace=True)
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            squad.drop(columns=[('Expected','/90'), ('Sweeper','#OPA/90')], inplace=True)
            vs.drop(columns=[('Expected','/90'), ('Sweeper','#OPA/90')], inplace=True)
            if normalize:
                keep_cols = [
                    ('Launched','Cmp%'), ('Passes','Launch%'), ('Passes','AvgLen'),
                    ('Goal Kicks','Launch%'), ('Goal Kicks', 'AvgLen'), 
                    ('Crosses','Stp%'), ('Sweeper','AvgDist')
                ]
                keep = squad[keep_cols]
                squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_shooting(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef shooting stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        print('Scraping {} {} shooting stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/shooting/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_shooting_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_shooting')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(columns=[('Standard','Sh/90'),('Standard','SoT/90')], inplace=True)
            df.drop(columns='Matches', level=1, inplace=True)
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            squad.drop(
                columns=[('Standard','Sh/90'), ('Standard','SoT/90')], 
                inplace=True
            )
            vs.drop(
                columns=[('Standard','Sh/90'), ('Standard','SoT/90')],
                inplace=True
            )
            if normalize:
                keep_cols = [('Standard','SoT%'), ('Standard','Dist')]
                keep = squad[keep_cols]
                squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_passing(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef passing stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif year < 2018:
            print('Passing stats not available from before the 2017/18 season.')
            return -1
        print('Scraping {} {} passing stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/passing/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_passing_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_passing')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(
                columns=[('Unnamed: 30_level_0','Matches')],
                inplace=True
            )
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            if normalize:
                keep_cols = [('Total','Cmp%'), ('Short','Cmp%'), ('Medium','Cmp%'), ('Long','Cmp%')]
                keep = squad[keep_cols]
                squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_passing_types(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef passing types stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif year < 2018:
            print('Passing type stats not available from before the 2017/18 season.')
            return -1
        print('Scraping {} {} passing type stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/passing_types/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_passing_types_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_passing_types')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(
                columns=[('Unnamed: 33_level_0','Matches')],
                inplace=True
            )
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            if normalize:
                squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
       
    ################################################################################
    def scrape_goal_shot_creation(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef goal and shot creation stats page of the chosen\
            league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif year < 2018:
            print('Goal and shot creation stats not available from before the 2017/18 season.')
            return -1
        print('Scraping {} {} goal and shot creation stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/gca/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_gca_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_gca')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            # df.drop(columns=[('SCA','SCA90'), ('GCA','GCA90')], inplace=True)
            df.drop(columns=['SCA90', 'GCA90', 'Matches'], level=1, inplace=True)
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            squad.drop(columns=[('SCA','SCA90'), ('GCA','GCA90')], inplace=True)
            vs.drop(columns=[('SCA','SCA90'), ('GCA','GCA90')], inplace=True)
            if normalize:
                squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_defensive(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef defensive stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif year < 2018:
            print('Defensive stats not available from before the 2017/18 season.')
            return -1
        print('Scraping {} {} defending stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/defense/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_defense_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_defense')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(
                columns=[('Unnamed: 31_level_0','Matches')],
                inplace=True
            )
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            if normalize:
                keep_cols = [('Vs Dribbles','Tkl%'), ('Pressures','%')]
                keep = squad[keep_cols]
                squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_possession(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef possession stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        elif year < 2018:
            print('Possession stats not available from before the 2017/18 season.')
            return -1
        print('Scraping {} {} possession stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/possession/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_possession_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_possession')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(
                columns=[('Unnamed: 32_level_0','Matches')],
                inplace=True
            )
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            if normalize:
                keep_cols = [('Dribbles','Succ%'),('Receiving','Rec%')]
                keep = squad[keep_cols]
                squad.iloc[:,4:] = squad.iloc[:,4:].divide(squad[('Unnamed: 3_level_0','90s')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,4:] = vs.iloc[:,4:].divide(vs[('Unnamed: 3_level_0','90s')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_playing_time(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef playing time stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        print('Scraping {} {} playing time stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/playingtime/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_playing_time_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_playing_time')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(columns=('Team Success','+/-90'), inplace=True)
            df.drop(columns='Matches', level=1, inplace=True)
            if year >= 2018:
                df.drop(columns='xG+/-90', level=1, inplace=True)
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            squad.drop(columns=('Team Success','+/-90'), inplace=True)
            vs.drop(columns=('Team Success','+/-90'), inplace=True)
            if year >= 2018:
                squad.drop(columns=('Team Success (xG)','xG+/-90'), inplace=True)
                vs.drop(columns=('Team Success (xG)','xG+/-90'), inplace=True)
            if normalize:
                keep_cols = [
                    ('Playing Time','Mn/MP'), ('Playing Time','Min%'),
                    ('Playing Time','90s'), ('Starts','Mn/Start')
                ]
                keep = squad[keep_cols]
                squad.iloc[:,4:] = squad.iloc[:,4:].divide(squad[('Playing Time','MP')], axis='rows')
                squad[keep_cols] = keep
                keep = vs[keep_cols]
                vs.iloc[:,4:] = vs.iloc[:,4:].divide(vs[('Playing Time','MP')], axis='rows')
                vs[keep_cols] = keep
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
    
    ################################################################################
    def scrape_misc(self, year, league, normalize=False, player=False):
        """ Scrapes the FBRef miscellaneous stats page of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player :bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : Pandas DataFrame
            DataFrame of the scraped stats
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        print('Scraping {} {} miscellaneous stats'.format(year, league))
        season = str(year-1)+'-'+str(year)
        url = self.get_season_link(year,league)
        new = url.split('/')
        new = '/'.join(new[:-1]) + '/misc/' + new[-1]
        new = new.replace('https','http')
        if player:
            # self.driver.get(new)
            self.get(new)
            if normalize:
                self.normalize_table('//*[@id=\'stats_misc_per_match_toggle\']')
            # get html and scrape table
            html = self.get_html_w_id('stats_misc')
            df = pd.read_html(html)[0]
            # drop duplicate header rows and link to match logs
            df = df[df[('Unnamed: 0_level_0','Rk')]!='Rk'].reset_index(drop=True)
            df.drop(columns='Matches', level=1, inplace=True)
            # convert type from str to float
            for col in list(df.columns.get_level_values(0)):
                if 'Unnamed' not in col:
                    df[col] = df[col].astype('float')
            df = self.add_player_ids_and_links(df, new) # get player IDs
            return df
        else:
            df = pd.read_html(new)
            squad = df[0].copy()
            vs = df[1].copy()
            if normalize:
                if year >= 2018:
                    keep_cols = [('Aerial Duels','Won%')]
                    keep = squad[keep_cols]
                    squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                    squad[keep_cols] = keep
                    keep = vs[keep_cols]
                    vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
                    vs[keep_cols] = keep
                else:
                    squad.iloc[:,3:] = squad.iloc[:,3:].divide(squad[('Unnamed: 2_level_0','90s')], axis='rows')
                    vs.iloc[:,3:] = vs.iloc[:,3:].divide(vs[('Unnamed: 2_level_0','90s')], axis='rows')
            # Get team IDs
            squad = self.add_team_ids(squad, 1, new, 'th') 
            vs = self.add_team_ids(vs, 1, new, 'th')
            return squad, vs
        
    ################################################################################
    def scrape_season(self, year, league, normalize=False, player=False):
        """ Scrapes all of the FBRef stats pages for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        player : bool
            OPTIONAL, default is False. If True, will scrape the player stats.\
            If False, will scrape team stats.
        Returns
        -------
        : dict
            Dict of the scraped stats pages. Keys are names of the stats pages\
            and values are Pandas DataFrames with the stats.
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        if year >= 2018:
            out = {
                'League Table':         self.scrape_league_table(year,league,normalize),
                'Standard':             self.scrape_standard(year,league,normalize,player),
                'Goalkeeping':          self.scrape_gk(year,league,normalize,player),
                'Advanced Goalkeeping': self.scrape_adv_gk(year,league,normalize,player),
                'Shooting':             self.scrape_shooting(year,league,normalize,player),
                'Passing':              self.scrape_passing(year,league,normalize,player),
                'Pass Types':           self.scrape_passing_types(year,league,normalize,player),
                'GCA':                  self.scrape_goal_shot_creation(year,league,normalize,player),
                'Defensive':            self.scrape_defensive(year,league,normalize,player),
                'Possession':           self.scrape_possession(year,league,normalize,player),
                'Playing Time':         self.scrape_playing_time(year,league,normalize,player),
                'Misc':                 self.scrape_misc(year,league,normalize,player)
            }
        else:
            out = {
                'League Table': self.scrape_league_table(year,league,normalize),
                'Standard':     self.scrape_standard(year,league,normalize,player),
                'Goalkeeping':  self.scrape_gk(year,league,normalize,player),
                'Shooting':     self.scrape_shooting(year,league,normalize,player),
                'Playing Time': self.scrape_playing_time(year,league,normalize,player),
                'Misc':         self.scrape_misc(year,league,normalize,player)
            }
        return out

    ################################################################################
    def scrape_matches(self, year, league, save=False):
        """ Scrapes the FBRef standard stats page of the chosen league season.
            
        Works by gathering all of the match URL's from the homepage of the\
        chosen league season on FBRef and then calling scrape_match() on each one.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        save : bool
            OPTIONAL, default is False. If True, will save the returned\
            DataFrame to a CSV file.
        Returns
        -------
        : Pandas DataFrame
            If save is False, will return the Pandas DataFrame with the the stats. 
        filename : str
            If save is True, will return the filename the CSV was saved to.
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        season = str(year-1)+'-'+str(year)
        links = self.get_match_links(year,league)
        
        matches = pd.DataFrame() # initialize df
        
        # scrape match data
        print('Scraping matches.')
        time.sleep(1)
        for link in tqdm(links):
            try:
                match = self.scrape_match(link)
                matches = pd.concat([matches, match], ignore_index=True)
            except Exception as E:
                print(f'Failed scraping match {link}')
                raise E
            
        # sort df by match date
        matches = matches.sort_values(by='Date').reset_index(drop=True)
        
        # save to CSV if requested by user
        if save:
            filename = f'{season}_{league.replace(" ","_")}_FBRef_matches.csv'
            matches.to_csv(path_or_buf=filename, index=False)
            print('Matches dataframe saved to ' + filename)
            return filename
        else:
            return matches
        
    ################################################################################    
    def scrape_match(self, link):
        """ Scrapes an FBRef match page.
        
        Args
        ----
        link : str
            URL to the FBRef match page
        Returns
        -------
        : Pandas DataFrame
            DataFrame containing most parts of the match page if they're\
            available (e.g. formations, lineups, scores, player stats, etc.).\
            The fields that are available vary by competition and year.
        """
        response = self.requests_get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #### Matchweek ####
        matchweek_el = list(soup.find('a', {'href': re.compile('-Stats')}, string=True).parents)[0]
        if '-Major-League-Soccer' in link:
            matchweek = matchweek_el\
                .getText()\
                .replace('Major League Soccer','')\
                .replace(')','')\
                .replace('(', '')\
                .strip()
        else:
            matchweek = int(
                matchweek_el\
                .getText()\
                .split('(')[-1]\
                .split(')')[0]\
                .lower()\
                .replace('matchweek','')\
                .strip()
            )

        #### Team names and ids ####
        team_els = [el.find('a') \
                for el in soup.find('div', {'class': 'scorebox'}).find_all('strong') \
                if el.find('a', href=True) is not None][:2]
        home_team_name = team_els[0].getText()
        home_team_id   = team_els[0]['href'].split('/')[3]
        away_team_name = team_els[1].getText()
        away_team_id   = team_els[1]['href'].split('/')[3]
        
        #### Scores ####
        scores = soup.find('div', {'class': 'scorebox'}).find_all('div', {'class': 'score'})

        #### Formations ####
        lineups = [pd.read_html(str(el.find('table')))[0] \
                   for el in soup.find_all('div', {'class': 'lineup'})]
        
        #### Player stats ####
        # Use table ID's to find the appropriate table. More flexible than xpath
        player_stats = dict()
        for i, (team, team_id) in enumerate([('Home',home_team_id), ('Away',away_team_id)]):

            summary = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_summary')})
            assert len(summary) < 2

            gk = soup.find_all('table', {'id': re.compile(f'keeper_stats_{team_id}')})
            assert len(gk) < 2

            passing = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing$')})
            assert len(passing) < 2

            pass_types = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing_types')})
            assert len(pass_types) < 2

            defense = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_defense')})
            assert len(defense) < 2

            possession = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_possession')})
            assert len(possession) < 2

            misc = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_misc')})
            assert len(misc) < 2

            player_stats[team] = {
                'Team Sheet': lineups[i] if len(lineups)!=0 else None,
                'Summary': pd.read_html(str(summary[0]))[0] if len(summary)==1 else None,
                'GK': pd.read_html(str(gk[0]))[0] if len(gk)==1 else None,
                'Passing': pd.read_html(str(passing[0]))[0] if len(passing)==1 else None,
                'Pass Types': pd.read_html(str(pass_types[0]))[0] if len(pass_types)==1 else None,
                'Defense': pd.read_html(str(defense[0]))[0] if len(defense)==1 else None,
                'Possession': pd.read_html(str(possession[0]))[0] if len(possession)==1 else None,
                'Misc': pd.read_html(str(misc[0]))[0] if len(misc)==1 else None,
            }

        #### Shots ####
        both_shots = soup.find_all('table', {'id': 'shots_all'})
        if len(both_shots) == 1:
            both_shots = pd.read_html(str(both_shots[0]))[0]
            both_shots = both_shots[~both_shots.isna().all(axis=1)]
        else:
            both_shots = None
        home_shots = soup.find_all('table', {'id': f'shots_{home_team_id}'})
        if len(home_shots) == 1:
            home_shots = pd.read_html(str(home_shots[0]))[0]
            home_shots = home_shots[~home_shots.isna().all(axis=1)]
        else:
            home_shots = None
        away_shots = soup.find_all('table', {'id': f'shots_{away_team_id}'})
        if len(away_shots) == 1:
            away_shots = pd.read_html(str(away_shots[0]))[0]
            away_shots = away_shots[~away_shots.isna().all(axis=1)]
        else:
            away_shots = None
            
        #### Expected stats flag ####
        expected = 'Expected' in player_stats['Home']['Summary'].columns.get_level_values(0)

        #### Build match series ####
        match = pd.Series(dtype=object)
        match['Link'] = link
        match['Date'] = datetime.strptime(
            str(soup.find('h1')).split('<br/>')[0].split('–')[-1].replace('</h1>','').strip(),
            '%A %B %d, %Y'
        ).date()
        match['Matchweek'] = matchweek
        match['Home Team'] = home_team_name
        match['Away Team'] = away_team_name
        match['Home Team ID'] = home_team_id
        match['Away Team ID'] = away_team_id
        match['Home Formation'] = (
            lineups[0].columns[0].split('(')[-1].replace(')','').strip() \
            if len(lineups)>0 else None
        )
        match['Away Formation'] = (
            lineups[1].columns[0].split('(')[-1].replace(')','').strip() 
            if len(lineups)>0 else None
        )
        match['Home Goals'] = int(scores[0].getText()) if scores[0].getText().isdecimal() else None
        match['Away Goals'] = int(scores[1].getText()) if scores[1].getText().isdecimal() else None
        match['Home Ast'] = player_stats['Home']['Summary'][('Performance','Ast')].values[-1]
        match['Away Ast'] = player_stats['Away']['Summary'][('Performance','Ast')].values[-1]
        match['Home xG']   = (
            player_stats['Home']['Summary'][('Expected','xG')].values[-1] 
            if expected else None
        )
        match['Away xG']   = (
            player_stats['Away']['Summary'][('Expected','xG')].values[-1] 
            if expected else None
        )
        match['Home npxG'] = (
            player_stats['Home']['Summary'][('Expected','npxG')].values[-1] 
            if expected else None
        )
        match['Away npxG'] = (
            player_stats['Away']['Summary'][('Expected','npxG')].values[-1] 
            if expected else None
        )
        match['Home xA']   = (
            player_stats['Home']['Summary'][('Expected','xA')].values[-1] 
            if expected else None
        )
        match['Away xA']   = (
            player_stats['Away']['Summary'][('Expected','xA')].values[-1] 
            if expected else None
        )
        match['Home Player Stats'] = pd.Series(player_stats['Home'])
        match['Away Player Stats'] = pd.Series(player_stats['Away'])
        match['Shots'] = pd.Series({
            'Both': both_shots,
            'Home': home_shots,
            'Away': away_shots,
        })
        
        match = match.to_frame().T
        
        return match
    
    ################################################################################
    def scrape_complete_scouting_reports(self, year, league, goalkeepers=False):
        """ Scrapes the FBRef scouting reports for all players in the chosen league\
            season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each\
            module.
        goalkeepers : bool
            OPTIONAL, default is False. If True, will scrape reports for only\
            goalkeepers. If False, will scrape reports for only outfield players.
        Returns
        -------
        per90 : Pandas DataFrame
            DataFrame of reports with Per90 stats.
        percentiles : Pandas DataFrame
            DataFrame of reports with stats percentiles (versus other players in\
            the top 5 leagues)
        """
        # Get the player links
        if goalkeepers:
            player_links = self.scrape_gk(year, league, player=True)['player_link']
        else:
            player_links = self.scrape_standard(year, league, player=True)['player_link']
        clear_output()
        
        # initialize dataframes
        per90_df = pd.DataFrame()
        percentiles_df = pd.DataFrame()
        
        # gather complete reports and append to dataframes
        cnt = 0
        for player_link in player_links:
            cnt += 1
            print('{}/{}'.format(cnt, len(player_links)), end='\r')
            _, per90, percentiles = self.complete_report_from_player_link(player_link)
            
            # skip goalkeers or players who don't have a complete report
            if (type(per90) is int) or (type(percentiles) is int) \
                    or not goalkeepers and per90['Position'].values[0]=='Goalkeepers':
                continue
                
            # append
            per90_df = per90_df.append(per90, ignore_index=True)
            percentiles_df = percentiles_df.append(percentiles, ignore_index=True)
        
        return per90_df, percentiles_df
    
    ################################################################################
    def complete_report_from_player_link(self, player_link):
        """ Scrapes the FBRef scouting reports for a player.
        
        Args
        ----
        player_link : str
            URL to an FBRef player page
        Returns
        -------
        complete_report : Pandas DataFrame
            Complete report, with stat names, Per90, and percentile values
        per90 : Pandas DataFrame
            Just the Per90 stat
        percentiles : Pandas DataFrame
            Just the percentile stats (versus layers in the otehr top 5 leagues)
        """
        # return -1 if the player has no scouting report
        player_link_html = urlopen(player_link).read().decode('utf8')
        if 'view complete scouting report' not in player_link_html.lower():
            return -1, -1, -1

        # Get the link to the complete report
        # self.driver.get(player_link)
        self.get(player_link)
        complete_report_button = self.driver.find_element(
            By.XPATH, 
            '/html/body/div[2]/div[6]/div[2]/div[1]/div/div/div[1]/div/ul/li[2]/a'
        )
        complete_report_link = complete_report_button.get_attribute('href')

        
        # self.driver.get(complete_report_link)
        self.get(complete_report_link)

        # Get the report table
        complete_report = pd.read_html(complete_report_link)[0]
        complete_report.columns = complete_report.columns.get_level_values(1)
        complete_report = pd.concat([
            pd.DataFrame(
                data={
                    'Statistic': ['Standard Stats','Statistic'], 
                    'Per 90': ['Standard Stats','Per 90'], 
                    'Percentile': ['Standard Stats', 'Percentile'],
                }
            ),
            complete_report,
        ])
        complete_report.dropna(axis=0, inplace=True)
        complete_report.reset_index(inplace=True, drop=True)

        # Get the table section headers and stats to make a multiindex
        header_idxs = [i for i in complete_report.index \
                       if np.all(complete_report.iloc[i,:]==complete_report.iloc[i,0])]
        header_idxs.append(complete_report.shape[0])
        table_headers = list()
        sub_stats = list()
        for i in range(len(header_idxs)-1):
            table_headers.append(complete_report.iloc[header_idxs[i],0])
            table = complete_report.iloc[header_idxs[i]+2:header_idxs[i+1], :].T
            sub_stats.append(list(table.iloc[0,:].values)) # sub stats are in first row
        idx = pd.MultiIndex.from_tuples([(table_headers[i], sub_stats[i][j]) \
                                         for i in range(len(table_headers)) \
                                         for j in range(len(sub_stats[i]))])
        
        # Initiate the dataframes
        per90 = pd.DataFrame(data=-1*np.ones([1,len(idx)]), columns=idx)
        percentiles = pd.DataFrame(data=-1*np.ones([1,len(idx)]), columns=idx)
        
        # Populate the dataframes
        for i in range(len(header_idxs)-1):
            table_header = complete_report.iloc[header_idxs[i],0]
            table = complete_report.iloc[header_idxs[i]+2:header_idxs[i+1], :].T
            table.columns = table.iloc[0,:]
            table = table.reset_index(drop=True).drop(index=0)
            for col in table.columns:
                per90[(table_header,col)] = float(table.loc[1,col].replace('%',''))
                percentiles[(table_header,col)] = int(table.loc[2,col])
        
        # add player names, positions, and minutes played
        player_name = ' '.join(complete_report_link.split('/')[-1].split('-')[:-2])
        player_pos = self.driver.find_element(By.XPATH, '//*[@class="filter switcher"]/div/a').text.replace('vs. ', '')
        minutes = int(self.driver.find_element(By.XPATH, '//*[@class="footer no_hide_long"]/div') \
                .text \
                .split(' minutes')[0] \
                .split(' ')[-1])
        per90['Player'] = player_name
        per90['Position'] = player_pos
        per90['Minutes'] = minutes
        percentiles['Player'] = player_name
        percentiles['Position'] = player_pos
        percentiles['Minutes'] = minutes

        return complete_report, per90, percentiles
        
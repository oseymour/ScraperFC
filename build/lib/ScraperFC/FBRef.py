from IPython.display import clear_output
import numpy as np
import pandas as pd
from ScraperFC.shared_functions import check_season, xpath_soup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import re
from datetime import datetime


class FBRef:
    """ ScraperFC module for FBRef
    """
    
    ############################################################################
    def __init__(self): #, driver='chrome'):
        # assert driver in ['chrome', 'firefox']
 
        self.wait_time = 5

        #if driver == 'chrome':
        from selenium.webdriver.chrome.service import Service as ChromeService
        options = Options()
        options.headless = True
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '+\
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 '+\
            'Safari/537.36'
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

        self.stats_categories = {
            'standard': {'url': 'stats', 'html': 'standard',},
            'goalkeeping': {'url': 'keepers', 'html': 'keeper',},
            'advanced goalkeeping': {'url': 'keepersadv','html': 'keeper_adv',},
            'shooting': {'url': 'shooting', 'html': 'shooting',},
            'passing': {'url': 'passing', 'html': 'passing',},
            'pass types': {'url': 'passing_types', 'html': 'passing_types',},
            'goal and shot creation': {'url': 'gca', 'html': 'gca',},
            'defensive': {'url': 'defense', 'html': 'defense',},
            'possession':  {'url': 'possession', 'html': 'possession',},
            'playing time': {'url': 'playingtime', 'html': 'playing_time',},
            'misc': {'url': 'misc', 'html': 'misc',},
        }
      
    ############################################################################
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

    ############################################################################
    def get(self, url):
        """ Custom get function just for the FBRef module. 
        
        Calls .get() from the Selenium WebDriver and then waits in order to\
        avoid a Too Many Requests HTTPError from FBRef. 
        
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
        : requests.Response
            The response
        """
        got_link = False 
        while not got_link:
            # Don't proceed until we've successfully retrieved the page
            response = requests.get(url)
            time.sleep(5)
            if response.status_code == 200:
                # 200 - OK
                # 403 - file not found
                # 500 - server error
                got_link = True
        return response
        

    ############################################################################
    def get_season_link(self, year, league):
        """ Returns the URL for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
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
                'finder': 'Premier-League-Stats',
            },
            'La Liga': {
                'url': 'https://fbref.com/en/comps/12/history/La-Liga-Seasons',
                'finder': 'La-Liga-Stats',
            },
            'Bundesliga': {
                'url': 'https://fbref.com/en/comps/20/history/Bundesliga-Seasons',
                'finder': 'Bundesliga-Stats',
            },
            'Serie A': {
                'url': 'https://fbref.com/en/comps/11/history/Serie-A-Seasons',
                'finder': 'Serie-A-Stats',
            },
            'Ligue 1': {
                'url': 'https://fbref.com/en/comps/13/history/Ligue-1-Seasons',
                'finder': 'Ligue-1-Stats' if year>=2003 else 'Division-1-Stats',
            },
            'MLS': {
                'url': 'https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons',
                'finder': 'Major-League-Soccer-Stats',
            },
        }
        url = urls_finders[league]['url']
        finder = urls_finders[league]['finder']
        
        # go to the league's history page
        response = self.requests_get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Generate season string to find right element
        season = str(year-1)+'-'+str(year) if league!='MLS' else str(year)
           
        # Get url to season
        for tag in soup.find_all('th', {'data-stat': 'year_id'}):
            if tag.find('a') \
                    and finder in tag.find('a')['href'] \
                    and tag.getText()==season:
                return 'https://fbref.com'+tag.find('a')['href']
            
        return -1 # if season URL is not found
    
    ############################################################################
    def get_match_links(self, year, league):
        """ Gets all match links for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        Returns
        -------
        : list
            FBRef links to all matches for the chosen league season
        """
        print('Gathering match links.')
        season_link = self.get_season_link(year, league)
        
        # go to the scores and fixtures page
        split = season_link.split('/')
        first_half = '/'.join(split[:-1])
        second_half = split[-1].split('-')
        second_half = '-'.join(second_half[:-1])+'-Score-and-Fixtures'
        fixtures_url = first_half+'/schedule/'+second_half
        
        response = self.requests_get(fixtures_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get links to all of the matches in that season
        finders = {
            'EPL': '-Premier-League',
           'La Liga': '-La-Liga',
           'Bundesliga': '-Bundesliga',
           'Serie A': '-Serie-A',
           'Ligue 1': '-Ligue-1' if year>=2003 else '-Division-1',
           'MLS': '-Major-League-Soccer'
        }
        finder = finders[league]
        
        match_links = [
            'https://fbref.com'+tag.find('a')['href'] 
            for tag 
            in soup.find_all('td', {'data-stat': 'score'}) 
            if tag.find('a') 
            and finder in tag.find('a')['href']
        ]
        
        return match_links

    ############################################################################
    def scrape_league_table(self, year, league):
        """ Scrapes the league table of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        Returns
        -------
        : Pandas DataFrame
            If league is not MLS, dataframe of the scraped league table
        : tuple
            If the league is MLS, a tuple of (west conference table, east \
            conference table). Both tables are dataframes.
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        print('Scraping {} {} league table'.format(year, league))
        
        season_url = self.get_season_link(year, league)
        response = self.requests_get(season_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        lg_table_html = soup.find_all('table', {'id': re.compile('overall')})

        if league != 'MLS':
            assert len(lg_table_html) == 1
            lg_table_html = lg_table_html[0]
            lg_table = pd.read_html(str(lg_table_html))[0]
            return lg_table

        else:
            assert len(lg_table_html) == 2
            east_table = pd.read_html(str(lg_table_html[0]))[0]
            west_table = pd.read_html(str(lg_table_html[1]))[0]
            return (east_table, west_table)
        
    ############################################################################
    def scrape_stats(self, year, league, stat_category, normalize=False):
        """ Scrapes a single stats category
        
        Adds team and player ID columns to the stats tables
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        stat_cateogry : str
            The stat category to scrape.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        Returns
        -------
        : tuple
            tuple of 3 Pandas DataFrames, (squad_stats, opponent_stats,\
            player_stats).
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        
        # Verify valid stat category
        if stat_category not in self.stats_categories.keys():
            raise Exception(f'"{stat_category}" is not a valid FBRef stats category. '+\
                            f'Must be one of {list(self.stats_categories.keys())}.')
        
        # Get URL to stat category
        season_url = self.get_season_link(year, league)
        old_suffix = season_url.split('/')[-1]
        new_suffix = f'{self.stats_categories[stat_category]["url"]}/{old_suffix}'
        new_url = season_url.replace(old_suffix, new_suffix)

        self.driver.get(new_url) # webdrive to link
        soup = BeautifulSoup(self.driver.page_source, 'html.parser') # get initial soup

        # Normalize, if requested
        if normalize:
            # click all per90 toggles on the page
            per90_toggles = soup.find_all('button', {'id': re.compile('per_match_toggle')})
            for toggle in per90_toggles:
                xpath = xpath_soup(toggle)
                button_el = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script('arguments[0].click()', button_el)
            # update the soup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Gather stats table tags
        squad_stats_tag = soup.find('table', {'id': re.compile('for')})
        opponent_stats_tag = soup.find('table', {'id': re.compile('against')})
        player_stats_tag = soup.find(
            'table', 
            {'id': re.compile(f'stats_{self.stats_categories[stat_category]["html"]}')}
        )
        
        # Get stats dataframes
        squad_stats = pd.read_html(str(squad_stats_tag))[0] if squad_stats_tag is not None else None
        opponent_stats = pd.read_html(str(opponent_stats_tag))[0] if opponent_stats_tag is not None else None
        player_stats = pd.read_html(str(player_stats_tag))[0] if player_stats_tag is not None else None
        
        # Drop duplicate header rows in player stats table
        if player_stats is not None:
            keep_rows_mask = player_stats[('Unnamed: 0_level_0','Rk')] != 'Rk'
            player_stats = player_stats[keep_rows_mask].reset_index(drop=True)
        
        # Add team ID's
        if squad_stats is not None:
            squad_stats['Team ID'] = [
                tag.find('a')['href'].split('/')[3] 
                for tag 
                in squad_stats_tag.find_all('th', {'data-stat': 'team'})[1:]
            ]
        if opponent_stats is not None:
            opponent_stats['Team ID'] = [
                tag.find('a')['href'].split('/')[3] 
                for tag 
                in opponent_stats_tag.find_all('th', {'data-stat': 'team'})[1:]
            ]
        
        # Add player ID's
        if player_stats is not None:
            player_stats['Player ID'] = [
                tag.find('a')['href'].split('/')[3] 
                for tag 
                in player_stats_tag.find_all('td', {'data-stat': 'player'})
            ]
        
        return squad_stats, opponent_stats, player_stats
    
    ############################################################################
    def scrape_all_stats(self, year, league, normalize=False):
        """ Scrapes all stat categories
        
        Runs scrape_stats() for each stats category on dumps the returned tuple\
        of dataframes into a dict.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        Returns
        -------
        : dict
            Keys are stat category names, values are tuples of 3 dataframes,\
            (squad_stats, opponent_stats, player_stats)
        """
        err, valid = check_season(year,league,'FBRef')
        if not valid:
            print(err)
            return -1
        
        return_package = dict()
        for stat_category in tqdm(self.stats_categories):
            stats = self.scrape_stats(year, league, stat_category, normalize)
            return_package[stat_category] = stats
            
        return return_package

    ############################################################################
    def scrape_matches(self, year, league, save=False):
        """ Scrapes the FBRef standard stats page of the chosen league season.
            
        Works by gathering all of the match URL's from the homepage of the\
        chosen league season on FBRef and then calling scrape_match() on each one.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
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
        
    ############################################################################
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
        team_els = [
            el.find('a') \
            for el 
            in soup.find('div', {'class': 'scorebox'}).find_all('strong') \
            if el.find('a', href=True) is not None
        ][:2]
        home_team_name = team_els[0].getText()
        home_team_id   = team_els[0]['href'].split('/')[3]
        away_team_name = team_els[1].getText()
        away_team_id   = team_els[1]['href'].split('/')[3]
        
        #### Scores ####
        scores = soup.find('div', {'class': 'scorebox'}).find_all('div', {'class': 'score'})

        #### Formations ####
        lineup_tags = [tag.find('table') for tag in soup.find_all('div', {'class': 'lineup'})]
        
        #### Player stats ####
        # Use table ID's to find the appropriate table. More flexible than xpath
        player_stats = dict()
        for i, (team, team_id) in enumerate([('Home',home_team_id), ('Away',away_team_id)]):

            summary_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_summary')})
            assert len(summary_tag) < 2
            summary_df = pd.read_html(str(summary_tag[0]))[0] if len(summary_tag)==1 else None

            gk_tag = soup.find_all('table', {'id': re.compile(f'keeper_stats_{team_id}')})
            assert len(gk_tag) < 2
            gk_df = pd.read_html(str(gk_tag[0]))[0] if len(gk_tag)==1 else None

            passing_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing$')})
            assert len(passing_tag) < 2
            passing_df = pd.read_html(str(passing_tag[0]))[0] if len(passing_tag)==1 else None

            pass_types_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing_types')})
            assert len(pass_types_tag) < 2
            pass_types_df = pd.read_html(str(pass_types_tag[0]))[0] if len(pass_types_tag)==1 else None

            defense_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_defense')})
            assert len(defense_tag) < 2
            defense_df = pd.read_html(str(defense_tag[0]))[0] if len(defense_tag)==1 else None

            possession_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_possession')})
            assert len(possession_tag) < 2
            possession_df = pd.read_html(str(possession_tag[0]))[0] if len(possession_tag)==1 else None

            misc_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_misc')})
            assert len(misc_tag) < 2
            misc_df = pd.read_html(str(misc_tag[0]))[0] if len(misc_tag)==1 else None
            
            lineup_df = pd.read_html(str(lineup_tags[i]))[0] if len(lineup_tags)!=0 else None
            
            #### Field player ID's for the stats tables ####
            if summary_df is not None:
                player_ids = [
                    tag.find('a')['href'].split('/')[3]
                    for tag 
                    in summary_tag[0].find_all('th', {'data-stat': 'player'})
                    if tag.find('a')
                ] 
                # Add empty string for the summary row at the bottom of the stats tables
                player_ids = player_ids + ['',]
                
                summary_df['Player ID'] = player_ids
                if passing_df is not None:
                    passing_df['Player ID'] = player_ids
                if pass_types_df is not None:
                    pass_types_df['Player ID'] = player_ids
                if defense_df is not None:
                    defense_df['Player ID'] = player_ids
                if possession_df is not None:
                    possession_df['Player ID'] = player_ids
                if misc_df is not None:
                    misc_df['Player ID'] = player_ids
            
            #### GK ID's ####
            if gk_df is not None:
                gk_ids = [
                    tag.find('a')['href'].split('/')[3]
                    for tag 
                    in gk_tag[0].find_all('th', {'data-stat': 'player'})
                    if tag.find('a')
                ]
                
                gk_df['Player ID'] = gk_ids

            #### Build player stats dict ####
            # This will be turned into a Series and then put into the match dataframe
            player_stats[team] = {
                'Team Sheet': lineup_df,
                'Summary': summary_df,
                'GK': gk_df,
                'Passing': passing_df,
                'Pass Types': pass_types_df,
                'Defense': defense_df,
                'Possession': possession_df,
                'Misc': misc_df,
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

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #### Build match series ####
        match = pd.Series(dtype=object)
        match['Link'] = link
        match['Date'] = datetime.strptime(
            str(soup.find('h1'))
                .split('<br/>')[0]
                .split('–')[-1] # not a normal dash, 
                .replace('</h1>','')
                .split('(')[0]
                .strip(),
            '%A %B %d, %Y'
        ).date()
        match['Matchweek'] = matchweek
        match['Home Team'] = home_team_name
        match['Away Team'] = away_team_name
        match['Home Team ID'] = home_team_id
        match['Away Team ID'] = away_team_id
        match['Home Formation'] = (
            player_stats['Home']['Team Sheet'].columns[0].split('(')[-1].replace(')','').strip()
            if player_stats['Home']['Team Sheet'] is not None else None
        )
        match['Away Formation'] = (
            player_stats['Away']['Team Sheet'].columns[0].split('(')[-1].replace(')','').strip()
            if player_stats['Away']['Team Sheet'] is not None else None
        )
        match['Home Goals'] = int(scores[0].getText()) if scores[0].getText().isdecimal() else None
        match['Away Goals'] = int(scores[1].getText()) if scores[1].getText().isdecimal() else None
        match['Home Ast'] = player_stats['Home']['Summary'][('Performance','Ast')].values[-1]
        match['Away Ast'] = player_stats['Away']['Summary'][('Performance','Ast')].values[-1]
        match['Home xG'] = player_stats['Home']['Summary'][('Expected','xG')].values[-1] if expected else None
        match['Away xG'] = player_stats['Away']['Summary'][('Expected','xG')].values[-1] if expected else None
        match['Home npxG'] = player_stats['Home']['Summary'][('Expected','npxG')].values[-1] if expected else None
        match['Away npxG'] = player_stats['Away']['Summary'][('Expected','npxG')].values[-1] if expected else None
        match['Home xA']   = player_stats['Home']['Summary'][('Expected','xA')].values[-1] if expected else None
        match['Away xA']   = player_stats['Away']['Summary'][('Expected','xA')].values[-1] if expected else None
        match['Home Player Stats'] = pd.Series(player_stats['Home'])
        match['Away Player Stats'] = pd.Series(player_stats['Away'])
        match['Shots'] = pd.Series({
            'Both': both_shots,
            'Home': home_shots,
            'Away': away_shots,
        })
        
        match = match.to_frame().T
        
        return match
    
    ############################################################################
    def scrape_complete_scouting_reports(self, year, league, goalkeepers=False):
        """ Scrapes the FBRef scouting reports for all players in the chosen league\
            season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
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
    
    ############################################################################
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
        
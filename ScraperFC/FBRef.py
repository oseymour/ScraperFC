from IPython.display import clear_output
import numpy as np
import pandas as pd
from ScraperFC.shared_functions import get_source_comp_info, xpath_soup, \
    NoMatchLinksException, UnavailableSeasonException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
import time
import re
from datetime import datetime
from io import StringIO
import warnings

class FBRef:
    """ ScraperFC module for FBRef
    """
    
    ####################################################################################################################
    def __init__(self):
 
        self.wait_time = 6 # in seconds, as of 30-Oct-2022 FBRef blocks if requesting more than 20 requests/minute

        options = Options()
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '+\
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 '+\
                             'Safari/537.36')
        options.add_argument('--incognito')
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options) 

        self.stats_categories = {'standard': {'url': 'stats', 'html': 'standard',},
                                 'goalkeeping': {'url': 'keepers', 'html': 'keeper',},
                                 'advanced goalkeeping': {'url': 'keepersadv','html': 'keeper_adv',},
                                 'shooting': {'url': 'shooting', 'html': 'shooting',},
                                 'passing': {'url': 'passing', 'html': 'passing',},
                                 'pass types': {'url': 'passing_types', 'html': 'passing_types',},
                                 'goal and shot creation': {'url': 'gca', 'html': 'gca',},
                                 'defensive': {'url': 'defense', 'html': 'defense',},
                                 'possession':  {'url': 'possession', 'html': 'possession',},
                                 'playing time': {'url': 'playingtime', 'html': 'playing_time',},
                                 'misc': {'url': 'misc', 'html': 'misc',},}
      
    ####################################################################################################################
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

    ####################################################################################################################
    def get(self, url):
        """ Custom get function just for the FBRef module. 
        
        Calls .get() from the Selenium WebDriver and then waits in order to avoid a Too Many Requests HTTPError from \
        FBRef. 
        
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
        
    ####################################################################################################################
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
        

    ####################################################################################################################
    def get_season_link(self, year, league):
        """ Returns the URL for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        Returns
        -------
        : str
            URL to the FBRef page of the chosen league season 
        """
        source_comp_info = get_source_comp_info(year,league,"FBRef")
        
        url = source_comp_info["FBRef"][league]["url"]
        finder = source_comp_info["FBRef"][league]["finder"]
        
        # go to the league's history page
        response = self.requests_get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        calendar_years = [str(year-1)+'-'+str(year), str(year)] # list of 1- and 2-calendar years strings to work for any competition
           
        # Get url to season
        for tag in soup.find_all("th", {"data-stat": ["year", "year_id"]}):
            finder_found = np.any([f in tag.find("a")["href"] for f in finder if tag.find("a")]) # bool, if any finders are found in tag
            season_found = np.any([tag.getText()==s for s in calendar_years]) # bool, if 1- or 2-calendar years are found in tag
            if tag.find("a") and finder_found and season_found:
                return "https://fbref.com"+tag.find("a")["href"]
        
        raise UnavailableSeasonException(year, league, "FBRef")
    
    ####################################################################################################################
    def get_match_links(self, year, league):
        """ Gets all match links for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        Returns
        -------
        : list
            FBRef links to all matches for the chosen league season
        """
        source_comp_info = get_source_comp_info(year,league,'FBRef')

        print(f'Gathering {year} {league} match links.')
        season_link = self.get_season_link(year, league)
        if season_link == -1:
            return None
        
        # go to the scores and fixtures page
        split = season_link.split('/')
        first_half = '/'.join(split[:-1])
        second_half = split[-1].split('-')
        second_half = '-'.join(second_half[:-1])+'-Score-and-Fixtures'
        fixtures_url = first_half+'/schedule/'+second_half
        response = self.requests_get(fixtures_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # check if there are any scores elements with links. if not, no match links are present
        scores_links = [t.find(href=True) for t in soup.find_all("td", {"data-stat": "score"}) if t.find(href=True)]
        if len(scores_links) == 0:
            raise NoMatchLinksException(fixtures_url, year, league)
        
        # find all of the match links from the scores and fixtures page that have the sources finder
        finders = source_comp_info["FBRef"][league]["finder"]
        match_links = ["https://fbref.com"+t["href"] for t in scores_links 
                       if t and np.any([f in t["href"] for f in finders])]
        
        return match_links

    ####################################################################################################################
    def scrape_league_table(self, year, league):
        """ Scrapes the league table of the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        Returns
        -------
        : Pandas DataFrame
            DataFrame may be empty if the league has no tables. Otherwise, the league table.
        : tuple
            If the league has multiple tables (e.g. Champions League, Liga MX, MLS) then a tuple of DataFrames will be returned.
        """
        _ = get_source_comp_info(year,league,'FBRef')

        print('Scraping {} {} league table'.format(year, league))
        
        season_url = self.get_season_link(year, league)
        response = self.requests_get(season_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        lg_table_html = soup.find_all('table', {'id': re.compile('overall')})
        
        if league == 'Ligue 2' and year == '2018':
            # 2018 Ligue 2 page has a small sub-table of the playoff qualifiers for some dumb reason
            lg_table_html = lg_table_html[:1]

        if len(lg_table_html) == 0:
            # Some compeitions have no tables (e.g. early women's champions league)
            warnings.warn(f'No league/group tables found for {year} {league}.')
            lg_table = pd.DataFrame()
        elif len(lg_table_html) == 1:
            # This will apply to most leagues
            lg_table = pd.read_html(StringIO(str(lg_table_html[0])))[0]
        else:
            # Some comps have multiple tables (champions league, liga mx, mls)
            warnings.warn(f'Multiple league/group tables found for {year} {league}.')
            lg_table = [pd.read_html(StringIO(str(html)))[0] for html in lg_table_html]

        return lg_table

        # if league == 'MLS':
        #     assert len(lg_table_html) == 2
        #     east_table = pd.read_html(StringIO(str(lg_table_html[0])))[0]
        #     west_table = pd.read_html(StringIO(str(lg_table_html[1])))[0]
        #     return (east_table, west_table)
        # elif league == 'Liga MX':
        #     apertura = pd.read_html(StringIO(str(lg_table_html[0])))[0]
        #     clausura = pd.read_html(StringIO(str(lg_table_html[1])))[0]
        #     lg_table = pd.read_html(StringIO(str(lg_table_html[2])))[0]
        #     rel_table = pd.read_html(StringIO(str(lg_table_html[3])))[0]
        #     return (apertura, clausura, lg_table, rel_table)
        # elif league == 'Ligue 2' and year == '2018':
        #     # 2018 Ligue 2 page has a small sub-table of the playoff qualifiers for some dumb reason
        #     lg_table_html = lg_table_html[0]
        #     lg_table = pd.read_html(StringIO(str(lg_table_html)))[0]
        #     return lg_table
        # elif league == 'Women Champions League' and year < 2024:
        #     warnings.warn('Women\'s Champions League has no group stage prior to 2024.')
        #     return pd.DataFrame()
        # else:
        #     assert len(lg_table_html) == 1
        #     lg_table_html = lg_table_html[0]
        #     lg_table = pd.read_html(StringIO(str(lg_table_html)))[0]
        #     return lg_table
        
    ####################################################################################################################
    def scrape_stats(self, year, league, stat_category, normalize=False):
        """ Scrapes a single stats category
        
        Adds team and player ID columns to the stats tables
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        stat_cateogry : str
            The stat category to scrape.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        Returns
        -------
        : tuple
            tuple of 3 Pandas DataFrames, (squad_stats, opponent_stats, player_stats).
        """
        _ = get_source_comp_info(year,league,'FBRef')
        
        # Verify valid stat category
        if stat_category not in self.stats_categories.keys():
            raise Exception(f'"{stat_category}" is not a valid FBRef stats category. '+\
                            f'Must be one of {list(self.stats_categories.keys())}.')
        
        season_url = self.get_season_link(year, league)
        
        if league == 'Big 5 combined':
            # Big 5 combined has separate pages for squad and player stats
            # Make the URLs to these pages
            first_half = '/'.join(season_url.split('/')[:-1])
            second_half = season_url.split('/')[-1]
            stats_category_url_filler = self.stats_categories[stat_category]['url']
            players_stats_url = '/'.join([first_half, stats_category_url_filler, 'players', second_half])
            squads_stats_url  = '/'.join([first_half, stats_category_url_filler, 'squads', second_half])
            
            # Get the soups from the 2 pages
            self.get(players_stats_url)
            players_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            self.get(squads_stats_url)
            squads_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Press normalize buttons, if requested
            if normalize:
                # click all per90 toggles on the SQUAD page first, since it's already loaded
                per90_toggles = squads_soup.find_all('button', {'id': re.compile('per_match_toggle')})
                for toggle in per90_toggles:
                    xpath = xpath_soup(toggle)
                    button_el = self.driver.find_element(By.XPATH, xpath)
                    self.driver.execute_script('arguments[0].click()', button_el)
                # update the soup
                squads_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                # Now do PLAYERS page
                self.get(players_stats_url)
                per90_toggles = players_soup.find_all('button', {'id': re.compile('per_match_toggle')})
                for toggle in per90_toggles:
                    xpath = xpath_soup(toggle)
                    button_el = self.driver.find_element(By.XPATH, xpath)
                    self.driver.execute_script('arguments[0].click()', button_el)
                # update the soup
                players_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Gather stats table tags
            squad_stats_tag = squads_soup.find('table', {'id': re.compile('for')})
            opponent_stats_tag = squads_soup.find('table', {'id': re.compile('against')})
            player_stats_tag = players_soup.find('table', {'id': re.compile(f'stats_{self.stats_categories[stat_category]["html"]}')})

            # Gather squad and opponent squad IDs
            # These are 'td' elements for Big 5
            squad_ids = [tag.find('a')['href'].split('/')[3] for tag 
                         in squad_stats_tag.find_all('td', {'data-stat': 'team'})
                         if tag and tag.find('a')]
            opponent_ids = [tag.find('a')['href'].split('/')[3] for tag 
                            in opponent_stats_tag.find_all('td', {'data-stat': 'team'})
                            if tag and tag.find('a')]

        else:
            # Get URL to stat category
            old_suffix = season_url.split('/')[-1] # suffix is last element 202X-202X-divider-stats
            new_suffix = f'{self.stats_categories[stat_category]["url"]}/{old_suffix}'
            new_url = season_url.replace(old_suffix, new_suffix)

            self.get(new_url) # webdrive to link
            soup = BeautifulSoup(self.driver.page_source, 'html.parser') # get initial soup

            # Normalize button, if requested
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
            player_stats_tag = soup.find('table', {'id': re.compile(f'stats_{self.stats_categories[stat_category]["html"]}')})

            # Gather squad and opponent squad IDs
            # These are 'th' elements for all other leagues
            squad_ids = [tag.find('a')['href'].split('/')[3] for tag 
                         in squad_stats_tag.find_all('th', {'data-stat': 'team'})[1:]
                         if tag and tag.find('a')]
            opponent_ids = [tag.find('a')['href'].split('/')[3] for tag 
                            in opponent_stats_tag.find_all('th', {'data-stat': 'team'})[1:]
                            if tag and tag.find('a')]
            
        # Get stats dataframes
        squad_stats = pd.read_html(StringIO(str(squad_stats_tag)))[0] if squad_stats_tag is not None else None
        opponent_stats = pd.read_html(StringIO(str(opponent_stats_tag)))[0] if opponent_stats_tag is not None else None
        player_stats = pd.read_html(StringIO(str(player_stats_tag)))[0] if player_stats_tag is not None else None

        # Drop rows that contain duplicated table headers, add team/player IDs
        if squad_stats is not None:
            squad_drop_mask = ~squad_stats.loc[:, (slice(None), 'Squad')].isna() & (squad_stats.loc[:, (slice(None), 'Squad')] != 'Squad')
            squad_stats = squad_stats[squad_drop_mask.values].reset_index(drop=True)
            squad_stats['Team ID'] = squad_ids
        
        if opponent_stats is not None:
            opponent_drop_mask = ~opponent_stats.loc[:, (slice(None), 'Squad')].isna() & (opponent_stats.loc[:, (slice(None), 'Squad')] != 'Squad')
            opponent_stats = opponent_stats[opponent_drop_mask.values].reset_index(drop=True)
            opponent_stats['Team ID'] = opponent_ids

        if player_stats is not None:
            keep_players_mask = (player_stats.loc[:, (slice(None), 'Rk')] != 'Rk').values
            player_stats = player_stats.loc[keep_players_mask, :].reset_index(drop=True)
        
        # Add player links and ID's
        if player_stats is not None:
            player_links = ['https://fbref.com' + tag.find('a')['href'] for tag 
                            in player_stats_tag.find_all('td', {'data-stat': 'player'})
                            if tag and tag.find('a')]
            player_stats['Player Link'] = player_links
            player_stats['Player ID'] = [l.split('/')[-2] for l in player_links]
        
        return squad_stats, opponent_stats, player_stats
    
    ####################################################################################################################
    def scrape_all_stats(self, year, league, normalize=False):
        """ Scrapes all stat categories
        
        Runs scrape_stats() for each stats category on dumps the returned tuple of dataframes into a dict.
        
        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        normalize : bool
            OPTIONAL, default is False. If True, will normalize all stats to Per90.
        Returns
        -------
        : dict
            Keys are stat category names, values are tuples of 3 dataframes, (squad_stats, opponent_stats, player_stats)
        """
        _ = get_source_comp_info(year,league,'FBRef')
        
        return_package = dict()
        for stat_category in tqdm(self.stats_categories):
            stats = self.scrape_stats(year, league, stat_category, normalize)
            return_package[stat_category] = stats
            
        return return_package

    ####################################################################################################################
    def scrape_matches(self, year, league, save=False):
        """ Scrapes the FBRef standard stats page of the chosen league season.
            
        Works by gathering all of the match URL's from the homepage of the chosen league season on FBRef and then \
        calling scrape_match() on each one.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        save : bool
            OPTIONAL, default is False. If True, will save the returned DataFrame to a CSV file.
        Returns
        -------
        : Pandas DataFrame
            If save is False, will return the Pandas DataFrame with the the stats. 
        filename : str
            If save is True, will return the filename the CSV was saved to.
        """
        _ = get_source_comp_info(year,league,'FBRef')
        
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
        
    ####################################################################################################################
    def scrape_match(self, link):
        """ Scrapes an FBRef match page.
        
        Args
        ----
        link : str
            URL to the FBRef match page
        Returns
        -------
        : Pandas DataFrame
            DataFrame containing most parts of the match page if they're available (e.g. formations, lineups, scores, \
            player stats, etc.). The fields that are available vary by competition and year.
        """
        response = self.requests_get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Matchweek/stage ==============================================================================================
        stage_el = list(soup.find('a', {'href': re.compile('-Stats')}, string=True).parents)[0]
        stage_text = stage_el.getText().split("(")[1].split(")")[0].strip()
        if "matchweek" in stage_text:
            stage = int(stage_text.lower().replace("matchweek","").strip())
        else:
            stage = stage_text

        # Team names and ids ===========================================================================================
        team_els = [el.find('a') for el 
                    in soup.find('div', {'class': 'scorebox'}).find_all('strong')
                    if el.find('a', href=True) is not None][:2]
        home_team_name = team_els[0].getText()
        home_team_id   = team_els[0]['href'].split('/')[3]
        away_team_name = team_els[1].getText()
        away_team_id   = team_els[1]['href'].split('/')[3]
        
        # Scores =======================================================================================================
        scores = soup.find('div', {'class': 'scorebox'}).find_all('div', {'class': 'score'})

        # Formations ===================================================================================================
        lineup_tags = [tag.find('table') for tag in soup.find_all('div', {'class': 'lineup'})]
        
        # Player stats =================================================================================================
        # Use table ID's to find the appropriate table. More flexible than xpath
        player_stats = dict()
        for i, (team, team_id) in enumerate([('Home',home_team_id), ('Away',away_team_id)]):

            summary_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_summary')})
            assert len(summary_tag) < 2
            summary_df = pd.read_html(StringIO(str(summary_tag[0])))[0] if len(summary_tag)==1 else None

            gk_tag = soup.find_all('table', {'id': re.compile(f'keeper_stats_{team_id}')})
            assert len(gk_tag) < 2
            gk_df = pd.read_html(StringIO(str(gk_tag[0])))[0] if len(gk_tag)==1 else None

            passing_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing$')})
            assert len(passing_tag) < 2
            passing_df = pd.read_html(StringIO(str(passing_tag[0])))[0] if len(passing_tag)==1 else None

            pass_types_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing_types')})
            assert len(pass_types_tag) < 2
            pass_types_df = pd.read_html(StringIO(str(pass_types_tag[0])))[0] if len(pass_types_tag)==1 else None

            defense_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_defense')})
            assert len(defense_tag) < 2
            defense_df = pd.read_html(StringIO(str(defense_tag[0])))[0] if len(defense_tag)==1 else None

            possession_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_possession')})
            assert len(possession_tag) < 2
            possession_df = pd.read_html(StringIO(str(possession_tag[0])))[0] if len(possession_tag)==1 else None

            misc_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_misc')})
            assert len(misc_tag) < 2
            misc_df = pd.read_html(StringIO(str(misc_tag[0])))[0] if len(misc_tag)==1 else None
            
            lineup_df = pd.read_html(StringIO(str(lineup_tags[i])))[0] if len(lineup_tags)!=0 else None
            
            # Field player ID's for the stats tables -------------------------------------------------------------------
            # Note: if a coach gets a yellow/red card, they appear in the player stats tables, in their own row, at the 
            # bottom.
            if summary_df is not None:
                player_ids = list()
                # Iterate across all els that are player/coach names in the summary stats table
                for tag in summary_tag[0].find_all('th', {'data-stat':'player', 'scope':'row', 'class':'left'}):
                    if tag.find('a'):
                        # if th el has an a subel, it should contain an href link to the player
                        player_id = tag.find('a')['href'].split('/')[3]
                    else:
                        # coaches and the summary row have now a subel (and no player id)
                        player_id = ''
                    player_ids.append(player_id)
                
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

            # GK ID's --------------------------------------------------------------------------------------------------
            if gk_df is not None:
                gk_ids = [tag.find('a')['href'].split('/')[3] for tag 
                          in gk_tag[0].find_all('th', {'data-stat': 'player'})
                          if tag.find('a')]
                gk_df['Player ID'] = gk_ids

            # Build player stats dict ----------------------------------------------------------------------------------
            # This will be turned into a Series and then put into the match dataframe
            player_stats[team] = {'Team Sheet': lineup_df, 'Summary': summary_df,
                                  'GK': gk_df, 'Passing': passing_df,
                                  'Pass Types': pass_types_df, 'Defense': defense_df,
                                  'Possession': possession_df, 'Misc': misc_df,}
            
        # Shots ========================================================================================================
        both_shots = soup.find_all('table', {'id': 'shots_all'})
        if len(both_shots) == 1:
            both_shots = pd.read_html(StringIO(str(both_shots[0])))[0]
            both_shots = both_shots[~both_shots.isna().all(axis=1)]
        else:
            both_shots = None
        home_shots = soup.find_all('table', {'id': f'shots_{home_team_id}'})
        if len(home_shots) == 1:
            home_shots = pd.read_html(StringIO(str(home_shots[0])))[0]
            home_shots = home_shots[~home_shots.isna().all(axis=1)]
        else:
            home_shots = None
        away_shots = soup.find_all('table', {'id': f'shots_{away_team_id}'})
        if len(away_shots) == 1:
            away_shots = pd.read_html(StringIO(str(away_shots[0])))[0]
            away_shots = away_shots[~away_shots.isna().all(axis=1)]
        else:
            away_shots = None
            
        # Expected stats flag ==========================================================================================
        expected = 'Expected' in player_stats['Home']['Summary'].columns.get_level_values(0)

        # Build match series ===========================================================================================
        match = pd.Series(dtype=object)
        match['Link'] = link
        match['Date'] = datetime.strptime(
            str(soup.find('h1'))
                .split('<br/>')[0]
                .split('–')[-1] # not a normal dash
                .replace('</h1>','')
                .split('(')[0]
                .strip(),
            '%A %B %d, %Y'
        ).date()
        match['Stage'] = stage
        match['Home Team'] = home_team_name
        match['Away Team'] = away_team_name
        match['Home Team ID'] = home_team_id
        match['Away Team ID'] = away_team_id
        match['Home Formation'] = (player_stats['Home']['Team Sheet'].columns[0].split('(')[-1].replace(')','').strip()
                                   if player_stats['Home']['Team Sheet'] is not None else None)
        match['Away Formation'] = (player_stats['Away']['Team Sheet'].columns[0].split('(')[-1].replace(')','').strip()
                                   if player_stats['Away']['Team Sheet'] is not None else None)
        match['Home Goals'] = int(scores[0].getText()) if scores[0].getText().isdecimal() else None
        match['Away Goals'] = int(scores[1].getText()) if scores[1].getText().isdecimal() else None
        match['Home Ast'] = player_stats['Home']['Summary'][('Performance','Ast')].values[-1]
        match['Away Ast'] = player_stats['Away']['Summary'][('Performance','Ast')].values[-1]
        match['Home xG'] = player_stats['Home']['Summary'][('Expected','xG')].values[-1] if expected else None
        match['Away xG'] = player_stats['Away']['Summary'][('Expected','xG')].values[-1] if expected else None
        match['Home npxG'] = player_stats['Home']['Summary'][('Expected','npxG')].values[-1] if expected else None
        match['Away npxG'] = player_stats['Away']['Summary'][('Expected','npxG')].values[-1] if expected else None
        match['Home xAG'] = player_stats['Home']['Summary'][('Expected','xAG')].values[-1] if expected else None
        match['Away xAG'] = player_stats['Away']['Summary'][('Expected','xAG')].values[-1] if expected else None
        match['Home Player Stats'] = pd.Series(player_stats['Home']).to_frame().T
        match['Away Player Stats'] = pd.Series(player_stats['Away']).to_frame().T
        match['Shots'] = pd.Series({'Both': both_shots, 'Home': home_shots, 'Away': away_shots,}).to_frame().T
        
        match = match.to_frame().T # series to dataframe
        
        return match
    
    ####################################################################################################################
    def scrape_complete_scouting_reports(self, year, league, goalkeepers=False):
        """ Scrapes the FBRef scouting reports for all players in the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        goalkeepers : bool
            OPTIONAL, default is False. If True, will scrape reports for only goalkeepers. If False, will scrape \
            reports for only outfield players.
        Returns
        -------
        per90 : Pandas DataFrame
            DataFrame of reports with Per90 stats.
        percentiles : Pandas DataFrame
            DataFrame of reports with stats percentiles (versus other players in the top 5 leagues)
        """
        # Get the player links
        if goalkeepers:
            player_links = self.scrape_stats(year, league, 'goalkeeping')[2]['Player Link'].values
        else:
            player_links = self.scrape_stats(year, league, 'standard')[2]['Player Link'].values
        
        # initialize dataframes
        per90_df = pd.DataFrame()
        percentiles_df = pd.DataFrame()
        
        # gather complete reports and append to dataframes
        for player_link in tqdm(player_links):
            report, name, pos, mins = self.complete_report_from_player_link(player_link)
            # skip players without reports
            if type(report) is int and report==-1:
                continue
            
            # separate per90 and percentiles and add player name, position, and minutes
            per90 = report['Per 90'].to_frame().T
            percentile = report['Percentile'].to_frame().T
            for col, val in [('Name',name), ('Position',pos), ('Minutes',mins)]:
                per90[col] = val
                percentile[col] = val
            
            # skip players who don't have a complete report or goalkeepers if scraping goalkeeper stats
            if (type(report) is int) or (not goalkeepers and per90['Position'].values[0]=='Goalkeepers'):
                continue
                
            # append
            per90_df = pd.concat([per90_df, per90], ignore_index=True)
            percentiles_df = pd.concat([percentiles_df, percentile], ignore_index=True)
        
        return per90_df, percentiles_df
    
    ####################################################################################################################
    def complete_report_from_player_link(self, player_link):
        """ Scrapes the FBRef scouting reports for a player.
        
        Args
        ----
        player_link : str
            URL to an FBRef player page
        Returns
        -------
        cleaned_complete_report : Pandas DataFrame
            Complete report with a MultiIndex of stats categories and statistics. Columns for per90 and percentile values.
        player_name : str
        player_pos : str
        minutes : int
        """
        # return -1 if the player has no scouting report
        player_link_html = urlopen(player_link).read().decode('utf8')
        if 'view complete scouting report' not in player_link_html.lower():
            cleaned_complete_report, player_name, player_pos, minutes = -1, -1, -1, -1
        else:
            # Get link to complete report
            soup = BeautifulSoup(requests.get(player_link).content, 'lxml')
            complete_report_link = soup\
                .find('div', {'id': re.compile('all_scout')})\
                .find('div', {'class': 'section_heading_text'})\
                .find('a', href=True)['href']
            complete_report_link = 'https://fbref.com' + complete_report_link
            self.get(complete_report_link)

            # Load and prelim clean of complete report
            soup = BeautifulSoup(requests.get(complete_report_link).content, 'lxml')
            complete_report = pd.read_html(StringIO(str(soup.find('table', {'id': re.compile('scout_full')}))))[0] # load report
            complete_report.columns = complete_report.columns.get_level_values(1) # drop top level column name
            complete_report.dropna(axis=0, inplace=True) # drop nan rows
            complete_report.reset_index(inplace=True, drop=True) # reset index

            # Row masks
            header_row_mask = complete_report.eq(complete_report.iloc[:,0], axis=0).all(1) # rows with stats category header names

            # Create multiindex column names broken down by stats category
            cleaned_complete_report = pd.DataFrame()
            stats_categories = ('Standard',) + tuple(complete_report[header_row_mask]['Statistic'].values)
            category_starts = [0,] + list(np.where(header_row_mask)[0]+2) # 2 to skip past category name row and col name row
            category_ends = list(np.where(header_row_mask)[0]-1) + [complete_report.shape[0]-1]
            for i in range(len(stats_categories)):
                temp = complete_report.loc[category_starts[i]:category_ends[i],:]
                temp.index = pd.MultiIndex.from_product([(stats_categories[i],), temp['Statistic']])
                cleaned_complete_report = pd.concat([cleaned_complete_report,temp])
            # drop statistic name column, it's in the multiindex now
            cleaned_complete_report.drop(columns='Statistic', inplace=True)
            cleaned_complete_report['Per 90'] = cleaned_complete_report['Per 90'].str.rstrip('%').astype('float')
            cleaned_complete_report['Percentile'] = cleaned_complete_report['Percentile'].astype(int)
            
            # Get player names, positions, and minutes played
            player_name = ' '.join(complete_report_link.split('/')[-1].split('-')[:-2])
            player_pos = soup\
                .find('div', {'id': re.compile('all_scout')})\
                .find('div', {'class': 'current'})\
                .text.split('vs.')[-1].strip()
            minutes = int(
                soup.find('div', {'id': re.compile('all_scout')})\
                    .find('div', {'class': 'footer no_hide_long'})\
                    .find('div')\
                    .text\
                    .split(' minutes')[0]\
                    .split(' ')[-1]
            )

        return cleaned_complete_report, player_name, player_pos, minutes
        
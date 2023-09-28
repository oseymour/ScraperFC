import datetime
import json
import numpy as np
import pandas as pd
from ScraperFC.shared_functions import get_source_comp_info
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from tqdm.auto import tqdm
import requests
from bs4 import BeautifulSoup
import time


class Understat:
    
    ####################################################################################################################
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(options=options)
        
        
    ####################################################################################################################
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()
        
        
    ####################################################################################################################
    def get_season_link(self, year, league):
        """ Gets URL of the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.

        Returns
        -------
        : str
            URL to the Understat page of the chosen league season.
        """
        lg = league.replace(" ","_")
        url = f"https://understat.com/league/{lg}/{str(year-1)}"
        return url
        
        
    ####################################################################################################################
    def get_match_links(self, year, league):
        """ Gets all of the match links for the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.

        Returns
        -------
        : list
            List of match links of the chosen league season
        """
        _ = get_source_comp_info(year,league,'Understat')
         
        base_url = "https://understat.com/"
        lg = league.replace(" ","_")
        url = base_url+"league/"+lg+"/"+str(year-1)
        self.driver.get(url)
        
        # Gather the links by hitting the "prev week" button until it's disabled
        links = set()
        btn = self.driver.find_element(By.CLASS_NAME, "calendar-prev")

        while "disabled" not in btn.get_attribute("outerHTML"):
            for el in self.driver.find_elements(By.CLASS_NAME, "match-info"):
                links.add(el.get_attribute("href"))
            btn.click()
            
        # One final collection for first week of season
        for el in self.driver.find_elements(By.CLASS_NAME, "match-info"):
            links.add(el.get_attribute("href"))
                
        # Remove Nones from the list of links 
        links = np.array(list(links))
        links = links[links!=None]

        return list(links)
    
    ####################################################################################################################
    def get_team_links(self, year, league):
        """ Gets all of the team links for the chosen league season

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.

        Returns
        -------
        : list
            List of team URL's from the chosen season.
        """
        team_links = set()
        self.driver.get(self.get_season_link(year, league))
        for el in self.driver.find_elements(By.TAG_NAME, 'a'):
            href = el.get_attribute('href')
            if href and 'team' in href:
                team_links.add(href)
        return list(team_links)
    
    
    ####################################################################################################################
    def remove_diff(self, string):
        """ Removes the plus/minus from some stats like xG.

        Args
        ----
        string : str
            The string to remove the difference from

        Returns
        -------
        : str
            String passed in as arg with the difference removed
        """
        string = string.split('-')[0]
        return float(string.split('+')[0])
    
    
    ####################################################################################################################
    def unhide_stats(self, columns):
        """ Understat doesn't display all stats by default. 
        
        This functions uses the stats currently shown in the table columns to\
        unhide stats that aren't being displayed.

        Args
        ----
        columns : Pandas DataFrame.columns
            The columns currently shown in the table being scraped

        Returns
        -------
        None
        """
        # Show the options popup
        options_button = self.driver.find_elements(By.CLASS_NAME, "options-button")[0]
        self.driver.execute_script("arguments[0].click()", options_button)
        
        # Iterate across all stats and show the ones that aren't in columns
        for el in self.driver.find_elements(By.CLASS_NAME, "table-options-row"):
            stat_name = el.find_element(By.CLASS_NAME, "row-title").text
            if (stat_name not in columns) and (stat_name != ""):
                el.find_element(By.CLASS_NAME, "row-display").click()

        # click the apply button
        self.driver.find_elements(By.CLASS_NAME, "button-apply")[0].click()
        
        return
        
        
    ####################################################################################################################
    def scrape_match(self, link):
        """ Scrapes a single match from Understat.

        Args
        ----
        link : str
            URL to the match

        Returns
        -------
        match : Pandas DataFrame
            The match stats
        """
        # self.driver.get(link)
        # soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        soup = BeautifulSoup(requests.get(link).content, 'html.parser')

        # Match ID and date ============================================================================================
        match_id = link.split('/')[-1]
        date = soup.find('div', {'class': 'page-wrapper'}).find_all('li')[-1].text
        date = datetime.datetime.strptime(date,'%b %d %Y').date()

        # Shots data ===================================================================================================
        shots_script = soup.find('div', {'class':'scheme-block', 'data-scheme':'chart'}).parent.find('script').text
        shots_data = shots_script.split('JSON.parse(\'')[1].split('\')')[0]
        shots_data = shots_data.encode('unicode_escape').replace(b'\\\\',b'\\').decode('unicode-escape')
        shots_data = json.loads(shots_data)
        shots_home_df = pd.json_normalize(shots_data['h'])
        shots_away_df = pd.json_normalize(shots_data['a'])
        all_shots_df = pd.concat([shots_home_df, shots_away_df], axis=0, ignore_index=True)
        all_shots_df['minute'] = all_shots_df['minute'].astype(int)
        all_shots_df = all_shots_df.sort_values('minute').reset_index(drop=True)

        # Team stats table =============================================================================================
        stats_scheme_block = soup.find_all('div', {'data-scheme':'stats'})
        assert len(stats_scheme_block) == 1
        stats_scheme_block = stats_scheme_block[0]
        # Team Names
        team_titles = stats_scheme_block.find(
            'div', {'class':'progress-bar teams-titles'}
        ).find_all(
            'div', {'class': 'progress-value'}
        )
        home_team, away_team = [x.text for x in team_titles]
        # Chances
        chances_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[1]
        home_chance = float(chances_bar.find('div', {'class':'progress-home'})['title'].replace('%',''))
        draw_chance = float(chances_bar.find('div', {'class':'progress-draw'})['title'].replace('%',''))
        away_chance = float(chances_bar.find('div', {'class':'progress-away'})['title'].replace('%',''))
        # Goals
        goals_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[2]
        home_goals, away_goals = [float(x.text) for x in goals_bar.find_all('div', {'class':'progress-value'})]
        # xG
        xg_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[3]
        home_xg, away_xg = [float(x.text) for x in xg_bar.find_all('div', {'class':'progress-value'})]
        # Shots
        shots_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[4]
        home_shots, away_shots = [float(x.text) for x in shots_bar.find_all('div', {'class':'progress-value'})]
        # Shots on Target
        sot_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[5]
        home_sot, away_sot = [float(x.text) for x in sot_bar.find_all('div', {'class':'progress-value'})]
        # DEEP
        deep_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[6]
        home_deep, away_deep = [float(x.text) for x in deep_bar.find_all('div', {'class':'progress-value'})]
        # PPDA
        ppda_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[7]
        home_ppda, away_ppda = [float(x.text) for x in ppda_bar.find_all('div', {'class':'progress-value'})]
        # xPTS
        xpts_bar = stats_scheme_block.find_all('div', {'class':'progress-bar'})[8]
        home_xpts, away_xpts = [float(x.text) for x in xpts_bar.find_all('div', {'class':'progress-value'})]

        # Player stats tables ==========================================================================================
        players_script = soup.find('div', {'id':'match-rosters'}).parent.find('script').text
        players_data = players_script.split('JSON.parse(\'')[1].split('\')')[0]
        players_data = players_data.encode('unicode_escape').replace(b'\\\\',b'\\').decode('unicode-escape')
        players_data = json.loads(players_data)
        players_home_df = pd.json_normalize(players_data['h'].values())
        players_away_df = pd.json_normalize(players_data['a'].values())

        # Build match df ===============================================================================================
        match = pd.Series(dtype=float)
        match['id'] = match_id
        match['date'] = date
        match['shots'] = all_shots_df
        match['home team'] = home_team
        match['away team'] = away_team
        match['home win proba'] = home_chance
        match['draw proba'] = draw_chance
        match['away win proba'] = away_chance
        match['home goals'] = home_goals
        match['away goals'] = away_goals
        match['home xG'] = home_xg
        match['away xG'] = away_xg
        match['home shots'] = home_shots
        match['away shots'] = away_shots
        match['home SoT'] = home_sot
        match['away SoT'] = away_sot
        match['home DEEP'] = home_deep
        match['away DEEP'] = away_deep
        match['home PPDA'] = home_ppda
        match['away PPDA'] = away_ppda
        match['home xPTS'] = home_xpts
        match['away xPTS'] = away_xpts
        match['home player stats'] = players_home_df
        match['away player stats'] = players_away_df
        match = match.to_frame().T

        return match
        
    ####################################################################################################################    
    def scrape_matches(self, year, league, save=False):
        """ Scrapes all of the matches from the chosen league season. 
        
        Gathers all match links from the chosen league season and then call\
            scrape_match() on each one.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        save : bool
            OPTIONAL, default False. If True, saves the DataFrame of match stats\
            to a CSV.

        Returns
        -------
        matches : Pandas DataFrame
            If save=False
        filename : str
            If save=True, the filename the DataFrame was saved to
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        season = str(year-1)+'-'+str(year)
        links = self.get_match_links(year, league)
        matches = pd.DataFrame()
        
        for link in tqdm(links):
            match = self.scrape_match(link)
            matches = pd.concat([matches, match], ignore_index=True, axis=0)
            time.sleep(2)
        
        # save to CSV if requested by user
        if save:
            filename = f'{season}_{league}_Understat_matches.csv'
            matches.to_csv(path_or_buf=filename, index=False)
            print('Matches dataframe saved to ' + filename)
            return filename
        else:
            return matches
        
        
    ####################################################################################################################
    def scrape_league_table(self, year, league, normalize=False):
        """ Scrapes the league table for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        normalize : bool 
            OPTIONAL, default False. If True, normalizes stats to per90

        Returns
        -------
        : Pandas DataFrame
            The league table of the chosen league season.
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        url = self.get_season_link(year, league) # link to the selected league/season
        self.driver.get(url)
        
        # Show all of the stats 
        # Get column names currently show in the table
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
        columns = pd.read_html(table)[0].columns
        self.unhide_stats(columns)

        # dataframe 
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
        df = pd.read_html(table)[0]
        
        # remove performance differential text from some columns
        for i in range(df.shape[0]):
            df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
            df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])
            df.loc[i,"xPTS"] = self.remove_diff(df.loc[i,"xPTS"])
            
        if normalize:
            df.iloc[:,3:14] = df.iloc[:,3:14].divide(df["M"], axis="rows")
            df.iloc[:,16:] = df.iloc[:,16:].divide(df["M"], axis="rows")
        
        self.close()
        self.__init__()
        return df
    
    
    ####################################################################################################################
    def scrape_home_away_tables(self, year, league, normalize=False):
        """ Scrapes the home and away league tables for the chosen league season.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23\
            season)
        league : str
            League. Look in shared_functions.py for the available leagues for\
            each module.
        normalize : bool 
            OPTIONAL, default False. If True, normalizes stats to per90

        Returns
        -------
        home : Pandas DataFrame
            Home league table
        away : Pandas DataFrame
            Away league table
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        url = self.get_season_link(year, league) # link to the selected league/season
        self.driver.get(url)

        # Show all of the stats
        # Get columns that are already shown
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        [el for el in labels if el.text=='home'][0].click()
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute('outerHTML')
        columns = pd.read_html(table)[0].columns 
        self.unhide_stats(columns)
        
        # Home Table
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        [el for el in labels if el.text=='home'][0].click()
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute('outerHTML')
        home = pd.read_html(table)[0]
        
        
        # Away Table
        [el for el in labels if el.text=='away'][0].click()
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute('outerHTML')
        away = pd.read_html(table)[0]
        
        # remove differentials from some columns
        for i in range(home.shape[0]):
            home.loc[i,"xG"] = self.remove_diff(home.loc[i,"xG"])
            home.loc[i,"xGA"] = self.remove_diff(home.loc[i,"xGA"])
            home.loc[i,"xPTS"] = self.remove_diff(home.loc[i,"xPTS"])
            away.loc[i,"xG"] = self.remove_diff(away.loc[i,"xG"])
            away.loc[i,"xGA"] = self.remove_diff(away.loc[i,"xGA"])
            away.loc[i,"xPTS"] = self.remove_diff(away.loc[i,"xPTS"])
        
        if normalize:
            home.iloc[:,3:14] = home.iloc[:,3:14].divide(home["M"], axis="rows")
            home.iloc[:,16:] = home.iloc[:,16:].divide(home["M"], axis="rows")
            away.iloc[:,3:14] = away.iloc[:,3:14].divide(away["M"], axis="rows")
            away.iloc[:,16:] = away.iloc[:,16:].divide(away["M"], axis="rows")
        
        self.close()
        self.__init__()
        return home, away
    
    
    ####################################################################################################################
    def scrape_situations(self, year, league):
        """ Scrapes the situations leading to shots for each team in the chosen\
            league season.

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
            DataFrame containing the situations
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)
                
        mi = pd.MultiIndex.from_product(
            [["Open play", "From corner", "Set piece", "Direct FK", "Penalty"],
             ["Sh", "G", "ShA", "GA", "xG", "xGA", "xGD", "xG/Sh", "xGA/Sh"]]
        )
        mi = mi.insert(0, ("Team names", "Team"))
        situations = pd.DataFrame()#columns=mi)
        
        for link in team_links:
            
            team_name = link.split("/")[-2]
            self.driver.get(link)
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            
            for i in range(df.shape[0]):
                # remove performance differential text from some columns
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])
            
            # reformat df to fit into a row
            df.drop(columns=["№","Situation"], inplace=True)
            row = df.to_numpy()
            row = np.insert(row, 0, team_name) # insert team name
            
            # append row
            situations = situations.append(
                pd.DataFrame(row.reshape(1,-1)),#, columns=situations.columns),
                ignore_index=True
            )
        
        situations.columns = mi
        self.close()
        self.__init__()
        return situations
    
    
    ####################################################################################################################
    def scrape_formations(self, year, league):
        """ Scrapes the stats for each team in the year and league, broken down\
            by formation used by the team.

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
        : dict
            Keys are each team. Values are more dicts with keys for each formation\
            and values are stats for each formation.
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)
        
        formations = dict()
        
        for link in team_links:
            
            # Get team name to add to formations
            team_name = link.split("/")[-2]
            if team_name not in formations.keys():
                formations[team_name] = dict()
                
            # Got to team's link, click formations, and get table of formations used
            self.driver.get(link)
            self.driver.find_element(
                By.XPATH, 
                "/html/body/div[1]/div[3]/div[3]/div/div[1]/div/label[2]"
            ).click()
            
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            df.drop(columns=["№"], inplace=True)
            
            # Remove performance differential text from some columns
            for i in range(df.shape[0]):
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])
                
                formation = df.loc[i,"Formation"]
                
                if formation not in formations[team_name].keys():
                    formations[team_name][formation] = df.iloc[i,:].drop(columns=["№","Formation"])                
                
        self.close()
        self.__init__()
        return formations
    
    
    ####################################################################################################################
    def scrape_game_states(self, year, league):
        """ Scrapes the game states for each team in the year and league

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
            DataFrame containing the game states
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)
                
        mi = pd.MultiIndex.from_product(
            [["Goal diff 0", "Goal diff -1", "Goal diff +1", "Goal diff < -1", "Goal diff > +1"],
             ["Min", "Sh", "G", "ShA", "GA", "xG", "xGA", "xGD", "xG90", "xGA90"]]
        )
        mi = mi.insert(0, ("Team names", "Team"))
        game_states = pd.DataFrame()#columns=mi)
        
        for link in team_links:
            
            team_name = link.split("/")[-2]
            self.driver.get(link)
            self.driver.find_element(
                By.XPATH, 
                "/html/body/div[1]/div[3]/div[3]/div/div[1]/div/label[3]"
            ).click()
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            df.drop(columns=["№"], inplace=True)
            
            row = {
                "Goal diff 0": None,
                "Goal diff -1": None,
                "Goal diff +1": None,
                "Goal diff < -1": None,
                "Goal diff > +1": None
            }
            for i in range(df.shape[0]):
                # remove performance differential text from some columns
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])
                
                game_state = df.loc[i,"Game state"]
                row[game_state] = df.loc[i,:].drop(labels=["Game state"])
                
            row_array = []
            for key in row.keys():
                row_array.append( row[key].to_numpy() )
            row_array = np.array(row_array)
            row_array = np.insert(row_array, 0, team_name) # insert team name
            
            # append row
            game_states = game_states.append(
                pd.DataFrame(row_array.reshape(1,-1)),#, columns=game_states.columns),
                ignore_index=True
            )
            
        game_states.columns = mi
        self.close()
        self.__init__()
        return game_states
    
    
    ####################################################################################################################
    def scrape_timing(self, year, league):
        """ Scrapes the timing of goals for each team in the year and league

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
            DataFrame containing the timing stats
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)

        mi = pd.MultiIndex.from_product(
            [["1-15", "16-30", "31-45", "46-60", "61-75", "76+"],
             ["Sh", "G", "ShA", "GA", "xG", "xGA", "xGD", "xG/Sh", "xGA/Sh"]]
        )
        mi = mi.insert(0, ("Team names", "Team"))
        timing_df = pd.DataFrame()#columns=mi)

        for link in team_links:
            
            team_name = link.split("/")[-2]
            self.driver.get(link)
            self.driver.find_element(
                By.XPATH, 
                "/html/body/div[1]/div[3]/div[3]/div/div[1]/div/label[4]"
            ).click()
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            df.drop(columns=["№"], inplace=True)

            row = {
                "1-15": None,
                "16-30": None,
                "31-45": None,
                "46-60": None,
                "61-75": None,
                "76+": None
            }
            for i in range(df.shape[0]):
                # remove performance differential text from some columns
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])

                timing = df.loc[i, "Timing"]
                row[timing] = df.loc[i,:].drop(labels=["Timing"])

            row_array = []
            for key in row.keys():
                row_array.append(row[key].to_numpy())
            row_array = np.array(row_array)
            row_array = np.insert(row_array, 0, team_name) # insert team name

            # append row
            timing_df = timing_df.append(
                pd.DataFrame(row_array.reshape(1,-1)),#, columns=timing_df.columns),
                ignore_index=True
            )
            
        timing_df.columns = mi
        self.close()
        self.__init__()
        return timing_df
    
    
    ####################################################################################################################
    def scrape_shot_zones(self, year, league):
        """ Scrapes the shot zones for each team in the year and league

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
            DataFrame containing the shot zones data
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)

        mi = pd.MultiIndex.from_product(
            [["Own goals", "Out of box", "Penalty area", "Six-yard box"],
             ["Sh", "G", "ShA", "GA", "xG", "xGA", "xGD", "xG/Sh", "xGA/Sh"]]
        )
        mi = mi.insert(0, ("Team names", "Team"))
        shot_zones_df = pd.DataFrame()#columns=mi)

        for link in team_links:
            
            team_name = link.split("/")[-2]
            self.driver.get(link)
            self.driver.find_element(
                By.XPATH, 
                "/html/body/div[1]/div[3]/div[3]/div/div[1]/div/label[5]"
            ).click()
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            df.drop(columns=["№"], inplace=True)

            row = {
                "Own goals": None,
                "Out of box": None,
                "Penalty area": None,
                "Six-yard box": None
            }
            for i in range(df.shape[0]):
                # remove performance differential text from some columns
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])

                zone = df.loc[i, "Shot zones"]
                row[zone] = df.loc[i,:].drop(labels=["Shot zones"])

            row_array = []
            for key in row.keys():
                if row[key] is None:
                    row[key] = pd.Series(np.zeros((9)))
                row_array.append(row[key].to_numpy())
            row_array = np.array(row_array)
            row_array = np.insert(row_array, 0, team_name) # insert team name

            # append row
            shot_zones_df = shot_zones_df.append(
                pd.DataFrame(row_array.reshape(1,-1)),#, columns=shot_zones_df.columns),
                ignore_index=True
            )
            
        shot_zones_df.columns = mi
        self.close()
        self.__init__()
        return shot_zones_df
    
    
    ####################################################################################################################
    def scrape_attack_speeds(self, year, league):
        """ Scrapes the attack speeds for each team in the year and league

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
            DataFrame containing the attack speeds of each team
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)

        mi = pd.MultiIndex.from_product(
            [["Normal", "Standard", "Slow", "Fast"],
             ["Sh", "G", "ShA", "GA", "xG", "xGA", "xGD", "xG/Sh", "xGA/Sh"]]
        )
        mi = mi.insert(0, ("Team names", "Team"))
        attack_speeds_df = pd.DataFrame()#columns=mi)

        for link in team_links:
            
            team_name = link.split("/")[-2]
            self.driver.get(link)
            self.driver.find_element(
                By.XPATH, 
                 "/html/body/div[1]/div[3]/div[3]/div/div[1]/div/label[6]"
            ).click()
            
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            df.drop(columns=["№"], inplace=True)

            row = {
                "Normal": None,
                "Standard": None,
                "Slow": None,
                "Fast": None
            }
            for i in range(df.shape[0]):
                # remove performance differential text from some columns
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])

                speed = df.loc[i, "Attack speed"]
                row[speed] = df.loc[i,:].drop(labels=["Attack speed"])

            row_array = []
            for key in row.keys():
                row_array.append(row[key].to_numpy())
            row_array = np.array(row_array)
            row_array = np.insert(row_array, 0, team_name) # insert team name

            # append row
            attack_speeds_df = attack_speeds_df.append(
                pd.DataFrame(row_array.reshape(1,-1)),#, columns=attack_speeds_df.columns),
                ignore_index=True
            )
            
        attack_speeds_df.columns = mi
        self.close()
        self.__init__()
        return attack_speeds_df
    
    
    ####################################################################################################################
    def scrape_shot_results(self, year, league):
        """ Scrapes the shot results for each team in the year and league

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
            DataFrame containing the shot results data
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        # Get links for teams in league that season
        team_links = self.get_team_links(year, league)

        mi = pd.MultiIndex.from_product(
            [["Missed shot", "Goal", "Saved shot", "Blocked shot", "Shot on post"],
             ["Sh", "G", "ShA", "GA", "xG", "xGA", "xGD", "xG/Sh", "xGA/Sh"]]
        )
        mi = mi.insert(0, ("Team names", "Team"))
        shot_results_df = pd.DataFrame()#columns=mi)

        for link in team_links:
            
            team_name = link.split("/")[-2]
            self.driver.get(link)
            self.driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div[3]/div/div[1]/div/label[7]").click()
            table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
            df = pd.read_html(table)[0]
            df.drop(columns=["№"], inplace=True)

            row = {
                "Missed shot": None,
                "Goal": None,
                "Saved shot": None,
                "Blocked shot": None,
                "Shot on post": None
            }
            for i in range(df.shape[0]):
                # remove performance differential text from some columns
                df.loc[i,"xG"] = self.remove_diff(df.loc[i,"xG"])
                df.loc[i,"xGA"] = self.remove_diff(df.loc[i,"xGA"])

                result = df.loc[i, "Result"]
                row[result] = df.loc[i,:].drop(labels=["Result"])

            row_array = []
            for key in row.keys():
                row_array.append(row[key].to_numpy())
            row_array = np.array(row_array)
            row_array = np.insert(row_array, 0, team_name) # insert team name

            # append row
            shot_results_df = shot_results_df.append(
                pd.DataFrame(row_array.reshape(1,-1)),
                # columns=shot_results_df.columns),
                ignore_index=True
            )
            
        shot_results_df.columns = mi
        self.close()
        self.__init__()
        return shot_results_df
            
        
    ####################################################################################################################
    def scrape_shot_xy(self, year, league, save=False, format='json'):
        """ Scrapes the info for every shot in the league and year.

        Args
        ----
        year : int
            Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
        league : str
            League. Look in shared_functions.py for the available leagues for each module.
        save : bool
            OPTIONAL, default if False. If True, shot XY's will be saved to a JSON file.
        format : str
            OPTIONAL, format of the output. Options are "json" and "dataframe"

        Returns
        -------
        : dict, Padnas DataFrame, or str
            Dict if save=False and format=json
            Dataframe if save=False and format=json
            Str if save=True. Filetype is determined by format argument
        """
        _ = get_source_comp_info(year,league,'Understat')
        
        season = str(year-1)+'-'+str(year)
        links = self.get_match_links(year, league)
        shots_data = dict()
        failures = list()

        for link in tqdm(links, desc='Shot XY'):
            
            match_id = link.split("/")[-1]
            try:
                game_shots_data = json.loads(
                    requests.get(link).text\
                        .split("shotsData")[1]\
                        .split("JSON.parse(\'")[1]\
                        .split("\')")[0]\
                        .encode("latin-1")\
                        .decode("unicode-escape")
                )
                shots_data[match_id] = game_shots_data
            except:
                failures.append(match_id)
                shots_data[match_id] = "Error scraping"
            
        self.close()
        self.__init__()
        
        # print any matches that scraping failed for
        if len(failures) != 0:
            print(f"Failed scraping the following matches: {failures}.")

        # Convert json to dataframe if requested
        if format == 'dataframe':
            shots_df = pd.DataFrame()
            for k in shots_data:
                for team in shots_data[k]:
                    shots_df = pd.concat([shots_df, pd.json_normalize(shots_data[k][team])], ignore_index=True, axis=0)
            shots_data = shots_df
        
        # Save shots data to file if requested
        if save:
            filename_prefix = f'{season}_{league}_shot_xy'
            if format == 'json':
                filename = filename_prefix + '.json'
                with open(filename, "w") as f:
                    f.write(json.dumps(shots_data))
            elif format == 'dataframe':
                filename = filename_prefix + '.csv'
                shots_data.to_csv(filename, index=False)
            print(f'Understat shot XY saved to {filename}.')
            shots_data = filename # return filename

        return shots_data

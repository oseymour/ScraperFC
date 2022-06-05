import datetime
import json
import numpy as np
import pandas as pd
from ScraperFC.shared_functions import check_season
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import requests


class Understat:
    
    ############################################################################
    def __init__(self):
        options = Options()
        options.headless = True
        options.add_argument("window-size=1400,600")
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        
        
    ############################################################################   
    def close(self):
        self.driver.close()
        self.driver.quit()
        
        
    ############################################################################    
    def get_season_link(self, year, league):
        """
        Gets URL of the season.
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: string, url of the year and league passed in
        """
        lg = league.replace(" ","_")
        url = f"https://understat.com/league/{lg}/{str(year-1)}"
        return url
        
        
    ############################################################################    
    def get_match_links(self, year, league):
        """
        Gets all of the match links for the league and year
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: set, match links
        """
        if not check_season(year,league,'Understat'):
            return -1
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
                
        return links
    
    ############################################################################
    def get_team_links(self, year, league):
        """
        Gets all of the team links for the league and year
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: set, links to teams' pages for the year
        """
        team_links = set()
        self.driver.get(self.get_season_link(year, league))
        for el in self.driver.find_elements(By.TAG_NAME, "a"):
            href = el.get_attribute("href")
            if href and "team" in href:
                team_links.add(href)
        return list(team_links)
    
    
    ############################################################################
    def remove_diff(self, string):
        """
        Removes the plus/minus from some stats like xG
        :param string: the string to remove the difference from
        :return: the string with the difference removed
        """
        string = string.split("-")[0]
        return float(string.split("+")[0])
    
    
    ############################################################################
    def unhide_stats(self, columns):
        """
        Understat doesn't display all stats by default. Uses the stats currently 
        shown in the table columns to unhide stats that aren't being displayed.
        :param columns: the columns currently shown in the table being scraped
        :return: None
        """
        # Show the options popup
        self.driver.find_elements(By.CLASS_NAME, "options-button")[0].click()
        
        # Iterate across all stats and show the ones that aren't in columns
        for el in self.driver.find_elements(By.CLASS_NAME, "table-options-row"):
            stat_name = el.find_element(By.CLASS_NAME, "row-title").text
            if (stat_name not in columns) and (stat_name != ""):
                el.find_element(By.CLASS_NAME, "row-display").click()

        # click the apply button
        self.driver.find_elements(By.CLASS_NAME, "button-apply")[0].click()
        
        return
        
        
    ############################################################################   
    def scrape_match(self, link):
        """
        Scrapes a single match from Understat.
        :param link: URL to the match
        :return: Pandas series of match stats
        """
        self.driver.get(link)
        
        elements = []
        for element in self.driver.find_elements(By.CLASS_NAME, "progress-value"):
            elements.append(element.get_attribute("innerHTML"))

        match = pd.Series()
        
        """ Match date and ID """
        for element in self.driver.find_elements(By.CLASS_NAME, "breadcrumb"):
            date = element.find_elements(By.TAG_NAME, "li")[2]
            date = date.text
        date = datetime.datetime.strptime(date,'%b %d %Y').date()
        match['date'] = date
        match['match id'] = link.split("/")[-1]


        """ Team Names """
        progress_values = [el.get_attribute("innerHTML") \
                           for el in self.driver.find_elements(By.CLASS_NAME, "progress-value")]
        match['home team'] = progress_values[0]
        match['away team'] = progress_values[1]


        """ Data from team stats table """
        # Go to team stats table
        [el for el in self.driver.find_elements(By.TAG_NAME, "label") \
         if "Stats" in el.text][0].click()
        # Each row in the stats table is a progress bar
        prog_bars = self.driver.find_elements(By.CLASS_NAME, "progress-bar")

        # Chances (separated out cuz it utilizes a draw element)
        bar = prog_bars[1]
        home = bar.find_element(By.CLASS_NAME, "progress-home").text
        try:
            draw = bar.find_element(By.CLASS_NAME, "progress-draw").text
        except NoSuchElementException:
            draw = "0%"
        away = bar.find_element(By.CLASS_NAME, "progress-away").text

        match["home win probability"] = float(home.replace("%","")) if home!="" else 0
        match["draw probability"]     = float(draw.replace("%","")) if draw!="" else 0
        match["away win probability"] = float(away.replace("%","")) if away!="" else 0

        # Goals, xG, shots, DEEP, PPDA, xPTS
        for bar in prog_bars[2:]:
            stat = bar.find_element(By.CLASS_NAME, "progress-title").text.lower()
            home = bar.find_element(By.CLASS_NAME, "progress-home").text
            away = bar.find_element(By.CLASS_NAME, "progress-away").text
            match[f"home {stat}"] = float(home)
            match[f"away {stat}"] = float(away)


        """ Data from player stats tables """
        #### Show all hidden stats ####
        columns = pd.read_html(self.driver.find_element(By.TAG_NAME, "table")\
                                          .get_attribute("outerHTML"))[0].columns
        self.unhide_stats(columns)

        #### Scrape player stats tables ####
        home_player_df = pd.read_html(self.driver.find_element(By.TAG_NAME, "table")\
                                                 .get_attribute("outerHTML"))[0]
        # Click button to go to away player stats table
        [el for el in self.driver.find_elements(By.TAG_NAME, "label") \
         if el.get_attribute("for")=="team-away"][0].click()
        away_player_df = pd.read_html(self.driver.find_element(By.TAG_NAME, "table")\
                                                 .get_attribute("outerHTML"))[0]

        #### Get the team sum stats that weren't gathered in the team stats table ####
        for team, temp in (("home", home_player_df), ("away", away_player_df)):
            for stat, column in (("key passes","KP"), 
                                 ("xa","xA"), 
                                 ("xgchain","xGChain"), 
                                 ("xgbuildup","xGBuildup")):
                match[f"{team} {stat}"] = self.remove_diff(str(temp.loc[temp.index[-1], column]))

        #### Remove No column, remove sum row, and remove diffs on xG and xA columns ####
        for player_df in (home_player_df, away_player_df):
            # drop sum row and No columns
            player_df.drop(index=player_df.index[-1], columns=player_df.columns[0], inplace=True) 
            # remove diffs
            player_df[["xG","xA"]] = player_df[["xG","xA"]].astype(str) # need to be str for remove_diff()
            player_df["xG"] = player_df.apply(lambda row : self.remove_diff(row["xG"]), axis=1)
            player_df["xA"] = player_df.apply(lambda row : self.remove_diff(row["xA"]), axis=1)

        #### Player stats dfs to match series ####
        match["home player stats"] = home_player_df
        match["away player stats"] = away_player_df
        
        return match
        
        
    ############################################################################    
    def scrape_matches(self, year, league, save=False):
        """
        Scrapes all of the matches from the passed year and league
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :param save: boolean, if true the output is saved to a CSV
        :return: Pandas DataFrame if not saved, filepath to CSV if saved
        """
        if not check_season(year,league,'Understat'):
            return -1
        
        season = str(year-1)+'-'+str(year)
        links = self.get_match_links(year, league)
        matches = pd.DataFrame()
        
        for link in tqdm(links):
#             print(link)
            match   = self.scrape_match(link)
            matches = matches.append(match, ignore_index=True)
        
        # save to CSV if requested by user
        if save:
            filename = season+"_"+league+"_Understat_matches.csv"
            matches.to_csv(path_or_buf=filename, index=False)
            print('Matches dataframe saved to ' + filename)
            return filename
        else:
            return matches
        
        
    ############################################################################    
    def scrape_league_table(self, year, league, normalize=False):
        """
        Scrapes the league table from the year passed in
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :param normalize: boolean, if true the output is normalized by the number
                          of matches played
        :return: Pandas DataFrame of the league table
        """
        if not check_season(year,league,'Understat'):
            return -1
        
        url = self.get_season_link(year, league) # link to the selected league/season
        self.driver.get(url)
        
        """ Show all of the stats """
        # Get column names currently show in the table
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute("outerHTML")
        columns = pd.read_html(table)[0].columns
        self.unhide_stats(columns)

        """ dataframe """
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
    
    
    ############################################################################
    def scrape_home_away_tables(self, year, league, normalize=False):
        """
        Scrapes the home and away league tables from the year passed in
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :param normalize: boolean, if true the output is normalized by the number
                          of matches played
        :return: home - the home league table, Pandas DataFrame
                 away - the away league table, Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
        url = self.get_season_link(year, league) # link to the selected league/season
        self.driver.get(url)

        """ Show all of the stats """
        # Get columns that are already shown
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        [el for el in labels if el.text=='home'][0].click()
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute('outerHTML')
        columns = pd.read_html(table)[0].columns 
        self.unhide_stats(columns)
        
        """ Home Table """
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        [el for el in labels if el.text=='home'][0].click()
        table = self.driver.find_elements(By.TAG_NAME, "table")[0].get_attribute('outerHTML')
        home = pd.read_html(table)[0]
        
        
        """ Away Table """
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
    
    
    ############################################################################
    def scrape_situations(self, year, league):
        """
        Scrapes the situations leading to shots for each team in the league and year
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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
    
    
    ############################################################################
    def scrape_formations(self, year, league):
        """
        Scrapes the stats for each team in the year and league, broken down by 
        formation used by the team.
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: dict, each team is a key and each team has their own dict for
                 each formation used
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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
    
    
    ############################################################################
    def scrape_game_states(self, year, league):
        """
        Scrapes the game states for each team in the year and league
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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
            
            row = {"Goal diff 0": None,
                   "Goal diff -1": None,
                   "Goal diff +1": None,
                   "Goal diff < -1": None,
                   "Goal diff > +1": None}
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
    
    
    ############################################################################
    def scrape_timing(self, year, league):
        """
        Scrapes the timing of goals for each team in the year and league
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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

            row = {"1-15": None,
                   "16-30": None,
                   "31-45": None,
                   "46-60": None,
                   "61-75": None,
                   "76+": None}
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
    
    
    ############################################################################
    def scrape_shot_zones(self, year, league):
        """
        Scrapes the shot zones for each team in the year and league
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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

            row = {"Own goals": None,
                   "Out of box": None,
                   "Penalty area": None,
                   "Six-yard box": None}
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
    
    
    ############################################################################
    def scrape_attack_speeds(self, year, league):
        """
        Scrapes the attack speeds for each team in the year and league
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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

            row = {"Normal": None,
                   "Standard": None,
                   "Slow": None,
                   "Fast": None}
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
    
    
    ############################################################################
    def scrape_shot_results(self, year, league):
        """
        Scrapes the shot results for each team in the year and league
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :return: Pandas DataFrame
        """
        if not check_season(year,league,'Understat'):
            return -1
        
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
            
        
    ############################################################################
    def scrape_shot_xy(self, year, league, save=False):
        """
        Scrapes the info for every shot in the league and year.
        :param year: int, calendary year the season ends in
        :param league: string, the league to be scraped
        :param save: boolean, if True output is saved to a JSON file
        :return: Pandas DataFrame if not saved, filepath to JSON if saved
        """
        if not check_season(year,league,'Understat'):
            return -1
        
        season = str(year-1)+'-'+str(year)
        links = self.get_match_links(year, league)
        shots_data = dict()
        failures = list()
        
        sum_time_selenium = 0
        sum_time_requests = 0

        for link in tqdm(links):
            
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
        print(f"Failed scraping the following matches: {failures}.")

        # save to JSON file
        if save:
            filename = f"{season}_{league}_shot_xy.json"
            with open(filename, "w") as f:
                f.write(json.dumps(shots_data))
            print(f'Scraping saved to {filename}')
            return filename
        else:
            return shots_data

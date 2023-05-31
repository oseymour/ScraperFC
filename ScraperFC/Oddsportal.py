from bs4 import BeautifulSoup
from datetime import datetime
import numpy as np
import pandas as pd
import re
from ScraperFC.shared_functions import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
import time
from tqdm.auto import tqdm
from webdriver_manager.chrome import ChromeDriverManager

class Oddsportal:
    """
    """

    ####################################################################################################################
    def __init__(self):
        options = Options()
        # options.headless = True
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images
        options.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )

    ####################################################################################################################
    def close(self):
        """ Closes and quits the Selenium WebDriver instance.
        """
        self.driver.close()
        self.driver.quit()

    ####################################################################################################################
    def get_match_links(self, year, league):
        """
        year=None for current season
        """
        check_season(year, league, 'Oddsportal')

        if not year:
            # current season
            url = sources['Oddsportal'][league]['url'] + '/results/'
        else:
            # previous season
            url = sources['Oddsportal'][league]['url'] + f'-{year-1}-{year}/results/'

        self.driver.get(url)
        html = self.driver.find_element(By.TAG_NAME, 'html')

        done = False
        all_links = list()
        while not done:
            # Get links on this page -----------------------------------------------------------------------------------
            soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
            page_links = [
                el['href'] for el in soup.find_all('a',{'class': re.compile('flex-col')}, href=True)
                if sources['Oddsportal'][league]['finder'] in el['href']
            ]

            # Keep paging down until we reach the bottom, collecting links on the way
            reached_bottom = False
            last_yoffset = -1
            while not reached_bottom:
                # Scroll down
                html.send_keys(Keys.PAGE_DOWN)

                # Find any new links
                soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
                page_links += [
                    el['href'] for el in soup.find_all('a',{'class': re.compile('flex-col')}, href=True)
                    if sources['Oddsportal'][league]['finder'] in el['href']
                    and el['href'] not in page_links
                ]
                
                # Check if we've reached the bottom
                new_yoffset = self.driver.execute_script('return window.pageYOffset;')
                if new_yoffset == last_yoffset:
                    reached_bottom = True
                else:
                    last_yoffset = new_yoffset

            all_links += page_links

            # Click the next button and got to the next page -----------------------------------------------------------
            next_button = [el for el in soup.find_all('p') if 'next'==el.text.lower()]
            if len(next_button) == 0:
                done = True
            else:
                next_button = self.driver.find_element(By.XPATH, xpath_soup(next_button[0]))
                self.driver.execute_script('arguments[0].scrollIntoView()', next_button)
                self.driver.execute_script('arguments[0].click()', next_button)
                
                # Wait for next or prev buttons to load
                loaded = False
                while not loaded:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
                    next_button = [el for el in soup.find_all('p') if 'next'==el.text.lower()]
                    prev_button = [el for el in soup.find_all('p') if 'prev'==el.text.lower()]
                    if next_button or prev_button:
                        loaded = True

        all_links = ['https://oddsportal.com' + l for l in all_links]

        return all_links

    ####################################################################################################################
    def scrape_match(self, url):
        self.driver.get(url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Date
        date = soup.find('div', {'class': re.compile('start-time')}).parent.text.replace('\xa0', ' ')
        # Replace 'Today' with day of the week
        if 'Today' in date:
            date = date.replace('Today', datetime.now().strftime('%A'))
        date = date.replace(',', ', ') # add spaces after commas
        date = datetime.strptime(date, '%A, %d %b %Y, %H:%M')

        # Team names
        imgs  = soup.find_all('img')
        teams = [
            img.parent.find('p').text for img in imgs 
            if img['src'] and 'team-logo' in img['src']
        ]
        team1 = teams[0]
        team2 = teams[1]
        
        # Goals and result
        final_result = [
            el.text for el in soup.find_all('strong') 
            if re.search('(?=.*Final)(?=.*result)', el.parent.text)
        ][0]
        goals1 = int(final_result.split(':')[0])
        goals2 = int(final_result.split(':')[1])
        result = '1' if goals1>goals2 else ('X' if goals1==goals2 else '2')

        match_df = pd.Series(dtype=object)
        match_df['Date'] = date
        match_df['Team1'] = team1
        match_df['Team2'] = team2
        match_df['Result'] = result
        match_df['Goals1'] = goals1
        match_df['Goals2'] = goals2
        match_df['Total goals'] = goals1 + goals2
        match_df = match_df.to_frame().T

        # Scrape odds
        moneyline_df = self.get_1X2odds_from_match(url)
        over_under_df = self.get_OUodds_from_match(url)

        # Format MultiIndices
        dfs_to_concat = [
            # (match_df, 'Info'), 
            (moneyline_df, '1X2'), 
            (over_under_df, 'O/U')
        ]
        max_levels = max([len(df.columns[0]) if type(df.columns) is not pd.Index else 1 for df,_ in dfs_to_concat])
        for df, name in dfs_to_concat:
            current_levels = len(df.columns[0]) if type(df.columns) is not pd.Index else 1

            # Add a name level to isolate different odds types
            name_level = pd.DataFrame([name for i in df.columns], index=df.columns)
            
            # Add empty levels so all MultiIndices have same number of levels
            empty_levels = pd.DataFrame([['']*(max_levels-current_levels) for i in df.columns], index=df.columns)
            
            # Combine all of the columns
            new_columns = pd.MultiIndex.from_frame(pd.concat([name_level, df.columns.to_frame(), empty_levels], axis=1))
            
            # Update columns in df object
            df.columns = new_columns

        # Actually merge the odds dfs now
        match_df = pd.concat([match_df, moneyline_df, over_under_df], axis=1)

        return match_df
    
    ####################################################################################################################
    def scrape_season_odds(self, year, league):
        raise NotImplementedError
        check_season(year, league, 'Oddsportal')

    ####################################################################################################################
    def get_1X2odds_from_match(self, url):
        # if '#1X2' not in url:
        #     url += '#1X2'
        self.driver.get(url)

        # Verify that odds are on the page
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        spanners_txt = [l.text for l in soup.find_all('span', {'class':'flex'})]
        if '1X2' not in spanners_txt:
            print(f'1X2 odds not found at {url}.')
            odds_df = pd.DataFrame()
        else:
            # Click on button for 1X2 odds
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            button_xpath = xpath_soup(soup.find('a', string='1X2'))
            button = self.driver.find_element(By.XPATH, button_xpath)
            self.driver.execute_script('arguments[0].click()', button)

            # Wait for page to load
            counter = 0
            while len(soup.find_all('div', {'class':'flex flex-col'})) == 0:
                if counter == 0:
                    raise Exception(f'Unable to load 1X2 odds from {url}.')
                soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
                time.sleep(1)
                counter += 1

            # # Hide inactive odds
            # hide_inactive_checkbox = [el for el in soup.find_all('label') if 'Hide inactive odds' in el.text][0].parent.find('input', {'type': 'checkbox'})
            # hide_inactive_checkbox = self.driver.find_element(By.XPATH, sfc.xpath_soup(hide_inactive_checkbox))
            # self.driver.execute_script('arguments[0].scrollIntoView', hide_inactive_checkbox)
            # self.driver.execute_script('arguments[0].click()', hide_inactive_checkbox)
            # time.sleep(0.5)
            # soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup

            odds_df = pd.Series(index=pd.MultiIndex(levels=[[],[]], codes=[[],[]]))
            odds_table = soup.find_all('div', {'class':'flex flex-col'})[1]
            rows = odds_table.find_all('div', {'class':re.compile('flex text-xs')})
            for row in rows:
                bookie_info = row.find_all('a')
                odds = row.find_all('div', recursive=False)

                # Skip some rows
                skip_conds = (
                    (len(odds) <= 1) # Odds not formatted right
                    or ('coupon' in odds[0].text.lower()) # Coupon row
                    or odds[4].text == ' - ' # Odds are crossed out (payout column is a dash)
                )
                if skip_conds:
                    continue

                # Odds 0 is the bookie info div
                odds1 = float(odds[1].text)
                oddsX = float(odds[2].text)
                odds2 = float(odds[3].text)
                payout_perc = float(odds[4].text.replace('%',''))

                if (len(bookie_info) <= 1):
                    # Average and max odds rows
                    agg_type = odds[0].text
                    # odds_df[f'{agg_type} 1'] = odds1
                    # odds_df[f'{agg_type} X'] = oddsX
                    # odds_df[f'{agg_type} 2'] = odds2
                    # odds_df[f'{agg_type} po %'] = payout_perc
                    odds_df[(agg_type, '1')] = odds1
                    odds_df[(agg_type, 'X')] = oddsX
                    odds_df[(agg_type, '2')] = odds2
                    odds_df[(agg_type, 'po %')] = payout_perc
                else:
                    # This is a row with odds from bookie
                    bookie_url = bookie_info[0]['href']
                    bookie_name = bookie_info[1].text
                    # bookie info 2 is the info button (link to oddsportal page for bookie)
                    # bookie info 3 is whether the bookie is running a bonus or not
                    # odds_df[f'{bookie_name} 1'] = odds1
                    # odds_df[f'{bookie_name} X'] = oddsX
                    # odds_df[f'{bookie_name} 2'] = odds2
                    # odds_df[f'{bookie_name} po %'] = payout_perc
                    odds_df[(bookie_name, '1')] = odds1
                    odds_df[(bookie_name, 'X')] = oddsX
                    odds_df[(bookie_name, '2')] = odds2
                    odds_df[(bookie_name, 'po %')] = payout_perc

            odds_df = odds_df.to_frame().T

        return odds_df

    ####################################################################################################################
    def get_OUodds_from_match(self, url):
        # if '#over-under' not in url:
        #     url += '#over-under'
        self.driver.get(url)

        # Verify that odds are on the page
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        spanners_txt = [l.text for l in BeautifulSoup(self.driver.page_source, 'html.parser').find_all('span', {'class':'flex'})]
        if 'Over/Under' not in spanners_txt:
            print(f'Over/Under odds not found at {url}.')
            odds_df = pd.DataFrame()
        else:
            # Click on button for Over/Under odds
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            button_xpath = xpath_soup(soup.find('a', string='Over/Under'))
            button = self.driver.find_element(By.XPATH, button_xpath)
            self.driver.execute_script('arguments[0].click()', button)

            # Wait for handicaps table to load
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            handicaps_table = soup.find_all('div', {'class':'min-md:px-[10px]'})
            counter = 0
            while len(handicaps_table) < 2:
                if counter == 10:
                    raise Exception(f'Unable to load over/under odds from {url}.')
                soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
                handicaps_table = soup.find_all('div', {'class':'min-md:px-[10px]'})
                time.sleep(1)
                counter += 1
            handicaps_table = handicaps_table[1]

            # # Hide inactive odds
            # hide_inactive_checkbox = [el for el in soup.find_all('label') if 'Hide inactive odds' in el.text][0].parent.find('input', {'type': 'checkbox'})
            # hide_inactive_checkbox = self.driver.find_element(By.XPATH, sfc.xpath_soup(hide_inactive_checkbox))
            # self.driver.execute_script('arguments[0].scrollIntoView', hide_inactive_checkbox)
            # self.driver.execute_script('arguments[0].click()', hide_inactive_checkbox)
            # time.sleep(0.5)
            # soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
        
            # odds_df = pd.Series(dtype=object)
            odds_df = pd.Series(index=pd.MultiIndex(levels=[[],[],[]], codes=[[],[],[]]))
            handicap_rows = handicaps_table.find_all('div', {'class':'relative flex flex-col'}, recursive=False)
            for handicap_row in handicap_rows:
                handicap = handicap_row.find('p').text.replace('Over/Under','').strip() # the total goals handicap text

                # Click on handicap row to expand odds
                handicap_row_button = self.driver.find_element(By.XPATH, xpath_soup(handicap_row.find('div')))
                self.driver.execute_script('arguments[0].scrollIntoView()', handicap_row_button)
                self.driver.execute_script('arguments[0].click()', handicap_row_button)

                # Wait for odds table to load
                loaded = False
                while not loaded:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
                    odds_table = soup.find_all('div', {'class': 'flex flex-col'})
                    if len(odds_table) > 0:
                        loaded = True

                soup = BeautifulSoup(self.driver.page_source, 'html.parser') # update soup
                odds_table = soup.find_all('div', {'class': 'flex flex-col'})[1]
                odds_rows = odds_table.find_all('div', {'class': re.compile('flex text-xs')})
                for odds_row in odds_rows:
                    bookie_info = odds_row.find_all('a')
                    odds = odds_row.find_all('div', recursive=False)

                    # Skip some rows
                    skip_conds = (
                        (len(odds) <= 1) # Odds not formatted right
                        or ('coupon' in odds[0].text.lower()) # Coupon row
                        or np.any([el.text==' - ' for el in odds]) # Odds are crossed out (payout column is a dash)
                    )
                    if skip_conds:
                        continue

                    if (len(bookie_info) <= 1):
                        # Average and max odds rows
                        agg_type = odds[0].text
                        over = None if odds[1].text=='-' else float(odds[1].text)
                        under = None if odds[2].text=='-' else float(odds[2].text)
                        payout_perc = float(odds[3].text.replace('%',''))
                        # odds_df[f'{agg_type} {handicap} over'] = over
                        # odds_df[f'{agg_type} {handicap} under'] = under
                        # odds_df[f'{agg_type} {handicap} po %'] = payout_perc
                        odds_df[(handicap, agg_type, 'over')] = over
                        odds_df[(handicap, agg_type, 'under')] = under
                        odds_df[(handicap, agg_type, 'po %')] = payout_perc
                    else:
                        # Row of bookie odds
                        # bookie_url = bookie_info[0]['href']
                        bookie_name = bookie_info[1].text
                        over = None if odds[2].text=='-' else float(odds[2].text)
                        under = None if odds[3].text=='-' else float(odds[3].text)
                        payout_perc = float(odds[4].text.replace('%',''))
                        # odds_df[f'{bookie_name} {handicap} over'] = over
                        # odds_df[f'{bookie_name} {handicap} under'] = under
                        # odds_df[f'{bookie_name} {handicap} po %'] = payout_perc
                        odds_df[(handicap, bookie_name, 'over')] = over
                        odds_df[(handicap, bookie_name, 'under')] = under
                        odds_df[(handicap, bookie_name, 'po %')] = payout_perc

                # Click on handicap row to collapse handicap odds
                self.driver.execute_script('arguments[0].scrollIntoView()', handicap_row_button)
                self.driver.execute_script('arguments[0].click()', handicap_row_button)

            odds_df = odds_df.to_frame().T

        return odds_df
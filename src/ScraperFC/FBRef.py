from bs4 import BeautifulSoup
import requests
from scraperfc_exceptions import InvalidYearException, InvalidLeagueException
import time
import numpy as np
import pandas as pd
import dateutil
from io import StringIO
import re
from tqdm import tqdm

stats_categories = {'standard': {'history url': 'stats', 'html': 'standard',},
                    'goalkeeping': {'history url': 'keepers', 'html': 'keeper',},
                    'advanced goalkeeping': {'history url': 'keepersadv','html': 'keeper_adv',},
                    'shooting': {'history url': 'shooting', 'html': 'shooting',},
                    'passing': {'history url': 'passing', 'html': 'passing',},
                    'pass types': {'history url': 'passing_types', 'html': 'passing_types',},
                    'goal and shot creation': {'history url': 'gca', 'html': 'gca',},
                    'defensive': {'history url': 'defense', 'html': 'defense',},
                    'possession':  {'history url': 'possession', 'html': 'possession',},
                    'playing time': {'history url': 'playingtime', 'html': 'playing_time',},
                    'misc': {'history url': 'misc', 'html': 'misc',},}

comps = {
    #################################
    # Men's club international cups
    'Copa Libertadores': {'history url': 'https://fbref.com/en/comps/14/history/Copa-Libertadores-Seasons',
                          'finders': ['Copa-Libertadores'],},
    'Champions League': {'history url': 'https://fbref.com/en/comps/8/history/Champions-League-Seasons',
                              'finders': ['European-Cup', 'Champions-League'],},
    'Europa League': {'history url': 'https://fbref.com/en/comps/19/history/Europa-League-Seasons',
                      'finders': ['UEFA-Cup', 'Europa-League'],},
    'Europa Conference League': {'history url': 'https://fbref.com/en/comps/882/history/Europa-Conference-League-Seasons',
                                 'finders': ['Europa-Conference-League'],},
    ####################################
    # Men's national team competitions
    'World Cup': {'history url': 'https://fbref.com/en/comps/1/history/World-Cup-Seasons',
                  'finders': ['World-Cup'],},
    'Copa America': {'history url': 'https://fbref.com/en/comps/685/history/Copa-America-Seasons',
                     'finders': ['Copa-America'],},
    'Euros': {'history url': 'https://fbref.com/en/comps/676/history/European-Championship-Seasons',
              'finders': ['UEFA-Euro', 'European-Championship'],},
    ###############
    # Men's big 5
    'Big 5 combined': {'history url': 'https://fbref.com/en/comps/Big5/history/Big-5-European-Leagues-Seasons',
                       'finders': ['Big-5-European-Leagues'],},
    'EPL': {'history url': 'https://fbref.com/en/comps/9/history/Premier-League-Seasons',
            'finders': ['Premier-League'],},
    'Ligue 1': {'history url': 'https://fbref.com/en/comps/13/history/Ligue-1-Seasons',
                'finders': ['Ligue-1', 'Division-1'],},
    'Bundesliga': {'history url': 'https://fbref.com/en/comps/20/history/Bundesliga-Seasons',
                   'finders': ['Bundesliga'],},
    'Serie A': {'history url': 'https://fbref.com/en/comps/11/history/Serie-A-Seasons',
                'finders': ['Serie-A'],},
    'La Liga': {'history url': 'https://fbref.com/en/comps/12/history/La-Liga-Seasons',
                'finders': ['La-Liga'],},
    #####################################
    # Men's domestic leagues - 1st tier
    'MLS': {'history url': 'https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons',
            'finders': ['Major-League-Soccer'],},
    'Brazilian Serie A': {'history url': 'https://fbref.com/en/comps/24/history/Serie-A-Seasons',
                          'finders': ['Serie-A'],},
    'Eredivisie': {'history url': 'https://fbref.com/en/comps/23/history/Eredivisie-Seasons',
                   'finders': ['Eredivisie'],},
    'Liga MX': {'history url': 'https://fbref.com/en/comps/31/history/Liga-MX-Seasons',
                'finders': ['Primera-Division', 'Liga-MX'],},
    'Primeira Liga': {'history url': 'https://fbref.com/en/comps/32/history/Primeira-Liga-Seasons',
                      'finders': ['Primeira-Liga'],},
    'Jupiler Pro League': {'history url': 'https://fbref.com/en/comps/37/history/Belgian-Pro-League-Seasons',
                           'finders': ['Belgian-Pro-League', 'Belgian-First-Division'],},
    'Argentina Liga Profesional': {'history url': 'https://fbref.com/en/comps/21/history/Primera-Division-Seasons',
                                   'finders': ['Primera-Division'],},
    ####################################
    # Men's domestic league - 2nd tier
    'EFL Championship': {'history url': 'https://fbref.com/en/comps/10/history/Championship-Seasons',
                         'finders': ['First-Division', 'Championship'],},
    'La Liga 2': {'history url': 'https://fbref.com/en/comps/17/history/Segunda-Division-Seasons',
                  'finders': ['Segunda-Division'],},
    '2. Bundesliga': {'history url': 'https://fbref.com/en/comps/33/history/2-Bundesliga-Seasons',
                      'finders': ['2-Bundesliga'],},
    'Ligue 2': {'history url': 'https://fbref.com/en/comps/60/history/Ligue-2-Seasons',
                'finders': ['Ligue-2'],},
    'Serie B': {'history url': 'https://fbref.com/en/comps/18/history/Serie-B-Seasons',
                'finders': ['Serie-B'],},
    #########################################
    # Women's internation club competitions
    'Women Champions League': {'history url': 'https://fbref.com/en/comps/181/history/Champions-League-Seasons',
                               'finders': ['Champions-League'],},
    ######################################
    # Women's national team competitions
    'Womens World Cup': {'history url': 'https://fbref.com/en/comps/106/history/Womens-World-Cup-Seasons',
                         'finders': ['Womens-World-Cup'],},
    'Womens Euros': {'history url': 'https://fbref.com/en/comps/162/history/UEFA-Womens-Euro-Seasons',
                     'finders': ['UEFA-Womens-Euro'],},
    ############################
    # Women's domestic leagues
    'NWSL': {'history url': 'https://fbref.com/en/comps/182/history/NWSL-Seasons',
             'finders': ['NWSL'],},
    'A-League Women': {'history url': 'https://fbref.com/en/comps/196/history/A-League-Women-Seasons',
                       'finders': ['A-League-Women', 'W-League'],},
    'WSL': {'history url': 'https://fbref.com/en/comps/189/history/Womens-Super-League-Seasons',
            'finders': ['Womens-Super-League'],},
    'D1 Feminine': {'history url': 'https://fbref.com/en/comps/193/history/Division-1-Feminine-Seasons',
                    'finders': ['Division-1-Feminine'],},
    'Womens Bundesliga': {'history url': 'https://fbref.com/en/comps/183/history/Frauen-Bundesliga-Seasons',
                          'finders': ['Frauen-Bundesliga'],},
    'Womens Serie A': {'history url': 'https://fbref.com/en/comps/208/history/Serie-A-Seasons',
                       'finders': ['Serie-A'],},
    'Liga F': {'history url': 'https://fbref.com/en/comps/230/history/Liga-F-Seasons',
               'finders': ['Liga-F'],},
    #########################
    # Women's domestic cups
    'NWSL Challenge Cup': {'history url': 'https://fbref.com/en/comps/881/history/NWSL-Challenge-Cup-Seasons',
                           'finders': ['NWSL-Challenge-Cup'],},
    'NWSL Fall Series': {'history url': 'https://fbref.com/en/comps/884/history/NWSL-Fall-Series-Seasons',
                         'finders': ['NWSL-Fall-Series'],},
}

class FBRef():

    #===========================================================================
    def __init__(self):
        return
    
    #===========================================================================
    
    def _get(self, url):
        """ Private, enforces a wait time to comply with FBRef's scraping time limits
        https://www.sports-reference.com/bot-traffic.html
        """
        wait_time = 6
        response = requests.get(url)
        time.sleep(wait_time)
        return response
    
    #===========================================================================
    def get_valid_seasons(self, league):
        """ Finds all of the valid years and their URLs for a given competition

        Args
        ----
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBRef
            module file and look at the keys.
        Returns
        -------
        : dict
            Returns a dict. Keys are valid years (as strings) and values are URLs
            that need to be appended to "https://fbref.com" to be a complete URL.
        """
        if type(league) is not str:
            raise TypeError('`league` must be a string.')
        if league not in comps:
            raise InvalidLeagueException(league=league, module='FBRef')
        
        url = comps[league]['history url']
        soup = BeautifulSoup(self._get(url).content, 'html.parser')

        season_urls = dict([(x.text, x.find('a')['href']) 
                            for x in soup.find_all('th', {'data-stat': True, 'class': True})
                            if x.find('a') is not None])
        
        return season_urls
    
    #===========================================================================
    def get_season_link(self, year, league):
        """ Returns the URL for the chosen league season.

        Args
        ----
        year : str
            The year to get. This needs to match the years on the "Competition History"
            page of the league. You can also call FBRef.get_valid_seasons(league)
            and see valid years in the keys of the returned dict.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBRef
            module file and look at the keys.
        Returns
        -------
        : str
            URL to the FBRef page of the chosen league season
        """
        if type(year) is not str:
            raise TypeError('`year` must be a string or int.')
        if type(league) is not str:
            raise TypeError('`league` must be a string.')
        if league not in comps:
            raise InvalidLeagueException(league=league, module='FBRef')
        
        seasons = self.get_valid_seasons(league)

        if year not in seasons:
            raise InvalidYearException(year, league)
        
        return 'https://fbref.com/' + seasons[year]
    
    #===========================================================================
    def get_match_links(self, year, league):
        """ Gets all match links for the chosen league season.

        Args
        ----
        year : str
            The year to get. This needs to match the years on the "Competition History"
            page of the league. You can also call FBRef.get_valid_seasons(league)
            and see valid years in the keys of the returned dict.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBRef
            module file and look at the keys.
        Returns
        -------
        : list
            FBRef links to all matches for the chosen league season
        """
        if type(year) is not str:
            raise TypeError('`year` must be a string or int.')
        if type(league) is not str:
            raise TypeError('`league` must be a string.')
        if league not in comps:
            raise InvalidLeagueException(league=league, module='FBRef')
        
        season_link = self.get_season_link(year, league)

        # Get the Scores and Fixtures page
        split = season_link.split('/')
        split.insert(-1, 'schedule')
        split[-1] = '-'.join(split[-1].split('-')[:-1])+'-Scores-and-Fixtures'
        fixtures_url = '/'.join(split)

        soup = BeautifulSoup(self._get(fixtures_url).content, 'html.parser')

        # Identify match links
        match_urls = list()
        possible_els = soup.find_all('td', {'class': True, 'data-stat': True})
        for x in possible_els:
            a = x.find('a')
            if a is not None and 'match' in a['href'] and np.any([f in a['href'] for f in comps[league]['finders']]):
                match_urls.append('https://fbref.com' + a['href'])
        match_urls = list(set(match_urls))
        return match_urls
    
    #===========================================================================
    def scrape_league_table(self, year, league):
        """ Scrapes the league table of the chosen league season

        Args
        ----
        year : str
            The year to get. This needs to match the years on the "Competition History"
            page of the league. You can also call FBRef.get_valid_seasons(league)
            and see valid years in the keys of the returned dict.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBRef
            module file and look at the keys.
        Returns
        -------
        : list
            Returns a list of all position tables from the league's homepage on
            FBRef. The first table will be the league table, all tables after that
            vary by competition.
        """
        season_link = self.get_season_link(year, league)
        tables = list()
        for df in pd.read_html(season_link):
            if 'Rk' in df.columns:
                # Remove all-NaN rows
                df = df.dropna(axis=0, how='all').reset_index(drop=True)

                # Add the df to tables
                tables.append(df)
        return tables
    
    #===========================================================================
    def scrape_match(self, link):
        """ Scrapes an FBRef match page.
        
        Args
        ----
        link : str
            URL to the FBRef match page
        Returns
        -------
        : Pandas DataFrame
            DataFrame containing most parts of the match page if they're available 
            (e.g. formations, lineups, scores, player stats, etc.). The fields 
            that are available vary by competition and year.
        """
        if type(link) is not str:
            raise TypeError('`link` must be a string.')

        soup = BeautifulSoup(self._get(link).content, 'html.parser')
        # Matchweek/stage ------------------------------------------------------
        stage_el = list(soup.find('a', {'href': re.compile('-Stats')}, string=True).parents)[0]
        stage_text = stage_el.getText().split('(')[1].split(')')[0].strip()
        if 'matchweek' in stage_text:
            stage = int(stage_text.lower().replace('matchweek','').strip())
        else:
            stage = stage_text

        # Team names and ids ---------------------------------------------------
        team_els = [el.find('a') for el 
                    in soup.find('div', {'class': 'scorebox'}).find_all('strong')
                    if el.find('a', href=True) is not None][:2]
        home_team_name = team_els[0].getText()
        home_team_id   = team_els[0]['href'].split('/')[3]
        away_team_name = team_els[1].getText()
        away_team_id   = team_els[1]['href'].split('/')[3]

        # Scores ---------------------------------------------------------------
        scores = soup.find('div', {'class': 'scorebox'}).find_all('div', {'class': 'score'})

        # Formations -----------------------------------------------------------
        lineup_tags = [tag.find('table') for tag in soup.find_all('div', {'class': 'lineup'})]

        # Player stats ---------------------------------------------------------
        # Use table ID's to find the appropriate table. More flexible than xpath
        player_stats = dict()
        for i, (team, team_id) in enumerate([('Home',home_team_id), ('Away',away_team_id)]):

            summary_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_summary')})
            assert len(summary_tag) < 2
            summary_df = pd.read_html(StringIO(str(summary_tag[0])))[0] \
                         if len(summary_tag)==1 else None

            gk_tag = soup.find_all('table', {'id': re.compile(f'keeper_stats_{team_id}')})
            assert len(gk_tag) < 2
            gk_df = pd.read_html(StringIO(str(gk_tag[0])))[0] \
                    if len(gk_tag)==1 else None

            passing_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing$')})
            assert len(passing_tag) < 2
            passing_df = pd.read_html(StringIO(str(passing_tag[0])))[0] \
                         if len(passing_tag)==1 else None

            pass_types_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_passing_types')})
            assert len(pass_types_tag) < 2
            pass_types_df = pd.read_html(StringIO(str(pass_types_tag[0])))[0] \
                            if len(pass_types_tag)==1 else None

            defense_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_defense')})
            assert len(defense_tag) < 2
            defense_df = pd.read_html(StringIO(str(defense_tag[0])))[0] \
                         if len(defense_tag)==1 else None

            possession_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_possession')})
            assert len(possession_tag) < 2
            possession_df = pd.read_html(StringIO(str(possession_tag[0])))[0] \
                            if len(possession_tag)==1 else None

            misc_tag = soup.find_all('table', {'id': re.compile(f'stats_{team_id}_misc')})
            assert len(misc_tag) < 2
            misc_df = pd.read_html(StringIO(str(misc_tag[0])))[0] \
                      if len(misc_tag)==1 else None
            
            lineup_df = pd.read_html(StringIO(str(lineup_tags[i])))[0] \
                        if len(lineup_tags)!=0 else None
            
            # Field player ID's for the stats tables ---------------------------
            # Note: if a coach gets a yellow/red card, they appear in the player 
            # stats tables, in their own row, at the  bottom.
            if summary_df is not None:
                player_ids = list()
                # Iterate across all els that are player/coach names in the summary stats table
                for tag in summary_tag[0].find_all('th', {'data-stat':'player', 
                                                          'scope':'row', 'class':'left'}):
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

            # GK ID's ----------------------------------------------------------
            if gk_df is not None:
                gk_ids = [tag.find('a')['href'].split('/')[3] 
                          for tag in gk_tag[0].find_all('th', {'data-stat': 'player'})
                          if tag.find('a')]
                gk_df['Player ID'] = gk_ids

            # Build player stats dict ------------------------------------------
            # This will be turned into a Series and then put into the match dataframe
            player_stats[team] = {'Team Sheet': lineup_df, 'Summary': summary_df,
                                  'GK': gk_df, 'Passing': passing_df,
                                  'Pass Types': pass_types_df, 'Defense': defense_df,
                                  'Possession': possession_df, 'Misc': misc_df,}
            
        # Shots ----------------------------------------------------------------
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
            
        # Expected stats flag --------------------------------------------------
        expected = 'Expected' in player_stats['Home']['Summary'].columns.get_level_values(0)

        # Build match series ---------------------------------------------------
        match = pd.Series(dtype=object)
        match['Link'] = link
        match['Date'] = dateutil.parser.parse(str(soup.find('h1'))
                                              .split('<br/>')[0]
                                              .split('–')[-1] # not a normal dash
                                              .replace('</h1>','')
                                              .split('(')[0]
                                              .strip())
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

    #===========================================================================
    def scrape_matches(self, year, league):
        """ Scrapes the FBRef standard stats page of the chosen league season.
            
        Works by gathering all of the match URL's from the homepage of the chosen 
        league season on FBRef and then calling scrape_match() on each one.

        Args
        ----
        year : str
            The year to get. This needs to match the years on the "Competition History"
            page of the league. You can also call FBRef.get_valid_seasons(league)
            and see valid years in the keys of the returned dict.
        league : str
            The league to retrieve valid seasons for. Examples include "EPL" and
            "La Liga". To see all possible options import `comps` from the FBRef
            module file and look at the keys.
        Returns
        -------
        : Pandas DataFrame
            Each row is the data from a single match.
        """
        matches_df = pd.DataFrame()
        match_links = self.get_match_links(year, league)
        for link in tqdm(match_links, desc=f'{year} {league} matches'):
            match_df = self.scrape_match(link)
            matches_df = pd.concat([matches_df, match_df], axis=0, ignore_index=True)

        # Sort matches by date
        matches_df = matches_df.sort_values(by='Date').reset_index(drop=True)

        return matches_df
        
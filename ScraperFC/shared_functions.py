from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from IPython.display import clear_output
import random
import pandas as pd
import numpy as np

########################################################################################################################
class InvalidSourceException(Exception):
    """ Raised when an invalid source is found
    """
    def __init__(self, source, source_comp_info):
        super().__init__()
        self.source = source
        self.source_comp_info = source_comp_info
    def __str__(self):
        return f"{self.source} is not a valid source. Must be one of {list(self.source_comp_info.keys())}."

########################################################################################################################
class InvalidLeagueException(Exception):
    """ Raised when an invalid league is found
    """
    def __init__(self, league, source, source_comp_info):
        super().__init__()
        self.league = league
        self.source = source
        self.source_comp_info = source_comp_info
    def __str__(self):
        return f"{self.league} is not a valid league for {self.source}. Options are {list(self.source_comp_info[self.source].keys())}."

########################################################################################################################
class InvalidYearException(Exception):
    """ Raised when an invalid year is found
    """
    def __init__(self, year, league, source, source_comp_info):
        super().__init__()
        self.year = year
        self.league = league
        self.source = source
        self.source_comp_info = source_comp_info
    def __str__(self):
        if self.source == "Sofascore":
            return f"{self.year} invalid for source {self.source} and league {self.league}. " +\
                f"Must be one of {list(self.source_comp_info[self.source][self.league]['seasons'].keys())}."
        else:
            return f"{self.year} invalid for source {self.source} and league {self.league}. " +\
                f"Must be {self.source_comp_info[self.source][self.league]['first valid year']} or later."

########################################################################################################################
class InvalidCurrencyException(Exception):
    """ Raised when an invalid currency is used with the Capology module.
    """
    def __init__(self):
        super().__init__()
    def __str__():
        return "Currency must be one of 'eur', 'gbp', or 'usd'."

########################################################################################################################
class UnavailableSeasonException(Exception):
    """ Raised when a given year and league is unavailable from a source.
    """
    def __init__(self, year, league, source):
        super().__init__()
        self.year = year
        self.league = league
        self.source = source
    def __str__(self):
        return f"No {self.league} {self.year} season is available on {self.source}."

########################################################################################################################
class NoMatchLinksException(Exception):
    """ Raised when no match links are found
    """
    def __init__(self, fixtures_url, year, league):
        super().__init__()
        self.fixtures_url = fixtures_url
        self.league = league
        self.year = year
    def __str__(self):
        return f"No match score elements with links found at {self.fixtures_url} for {self.year} {self.league}."

########################################################################################################################
def get_source_comp_info(year, league, source):
    """ Checks to make sure that the given league season is a valid season for 
    the scraper and returns the source_comp_info dict for use in the modules.
    
    Args
    ----
    year : int
        Calendar year that the season ends in (e.g. 2023 for the 2022/23 season)
    league : str
        League. Look in shared_functions.py for the available leagues for each\
        module.
    source : str
        The scraper to be checked (e.g. "FBRef", "Transfermarkt, etc.). These\
        are the ScraperFC modules.
    Returns
    -------
    souce_comp_info: dict
        Dict containing all of the competition info for all of the sources. Used
        for different things in every module
    """
    # Dict of data sources and leagues for each source
    source_comp_info = {
        "All": {},
        "FBRef": {
            # Each competition gets its first valid year (from the competition seasons history page on fbref), the url
            # to the season history page, and the "finder" which is used to find the season and match links in HTML
            #################################
            # Men"s club international cups #
            #################################
            "Copa Libertadores": {
                "first valid year": 2014,
                "url": "https://fbref.com/en/comps/14/history/Copa-Libertadores-Seasons",
                "finder": ["Copa-Libertadores"],
            },
            "Champions League": {
                "first valid year": 1991,
                "url": "https://fbref.com/en/comps/8/history/Champions-League-Seasons",
                "finder": ["European-Cup", "Champions-League"],
            },
            "Europa League": {
                "first valid year": 1991,
                "url": "https://fbref.com/en/comps/19/history/Europa-League-Seasons",
                "finder": ["UEFA-Cup", "Europa-League"],
            },
            "Europa Conference League": {
                "first valid year": 2022,
                "url": "https://fbref.com/en/comps/882/history/Europa-Conference-League-Seasons",
                "finder": ["Europa-Conference-League"],
            },
            ####################################
            # Men"s national team competitions #
            ####################################
            "World Cup": {
                "first valid year": 1930,
                "url": "https://fbref.com/en/comps/1/history/World-Cup-Seasons",
                "finder": ["World-Cup"],
            },
            "Copa America": {
                "first valid year": 2015,
                "url": "https://fbref.com/en/comps/685/history/Copa-America-Seasons",
                "finder": ["Copa-America"],
            },
            "Euros": {
                "first valid year": 2000,
                "url": "https://fbref.com/en/comps/676/history/European-Championship-Seasons",
                "finder": ["UEFA-Euro", "European-Championship"],
            },
            ###############
            # Men"s big 5 #
            ###############
            "Big 5 combined": {
                "first valid year": 1996,
                "url": "https://fbref.com/en/comps/Big5/history/Big-5-European-Leagues-Seasons",
                "finder": ["Big-5-European-Leagues"],
            },
            "EPL": {
                "first valid year": 1993,
                "url": "https://fbref.com/en/comps/9/history/Premier-League-Seasons",
                "finder": ["Premier-League"],
            },
            "Ligue 1": {
                "first valid year": 1996,
                "url": "https://fbref.com/en/comps/13/history/Ligue-1-Seasons",
                "finder": ["Ligue-1", "Division-1"],
            },
            "Bundesliga": {
                "first valid year": 1989,
                "url": "https://fbref.com/en/comps/20/history/Bundesliga-Seasons",
                "finder": ["Bundesliga"],
            },
            "Serie A": {
                "first valid year": 1989,
                "url": "https://fbref.com/en/comps/11/history/Serie-A-Seasons",
                "finder": ["Serie-A"],
            },
            "La Liga": {
                "first valid year": 1989,
                "url": "https://fbref.com/en/comps/12/history/La-Liga-Seasons",
                "finder": ["La-Liga"],
            },
            #####################################
            # Men"s domestic leagues - 1st tier #
            #####################################
            "MLS": {
                "first valid year": 1996,
                "url": "https://fbref.com/en/comps/22/history/Major-League-Soccer-Seasons",
                "finder": ["Major-League-Soccer"],
            },
            "Brazilian Serie A": {
                "first valid year": 2014,
                "url": "https://fbref.com/en/comps/24/history/Serie-A-Seasons",
                "finder": ["Serie-A"],
            },
            "Eredivisie": {
                "first valid year": 2001,
                "url": "https://fbref.com/en/comps/23/history/Eredivisie-Seasons",
                "finder": ["Eredivisie"],
            },
            "Liga MX": {
                "first valid year": 2004,
                "url": "https://fbref.com/en/comps/31/history/Liga-MX-Seasons",
                "finder": ["Primera-Division", "Liga-MX"],
            },
            "Primeira Liga": {
                "first valid year": 2001,
                "url": "https://fbref.com/en/comps/32/history/Primeira-Liga-Seasons",
                "finder": ["Primeira-Liga"],
            },
            "Jupiler Pro League": {
                "first valid year": 2004,
                "url": 'https://fbref.com/en/comps/37/history/Belgian-Pro-League-Seasons',
                "finder": ["Belgian-Pro-League"],
            },
            "Argentina Liga Profesional": {
                "first valid year": 2014,
                "url": 'https://fbref.com/en/comps/21/history/Primera-Division-Seasons',
                "finder": ['Primera-Division'],
            },
            ####################################
            # Men"s domestic league - 2nd tier #
            ####################################
            "EFL Championship": {
                "first valid year": 2002,
                "url": "https://fbref.com/en/comps/10/history/Championship-Seasons",
                "finder": ["First-Division", "Championship"],
            },
            "La Liga 2": {
                "first valid year": 2002,
                "url": 'https://fbref.com/en/comps/17/history/Segunda-Division-Seasons',
                "finder": ["Segunda-Division"],
            },
            "2. Bundesliga": {
                "first valid year": 2004,
                "url": 'https://fbref.com/en/comps/33/history/2-Bundesliga-Seasons',
                "finder": ['2-Bundesliga'],
            },
            "Ligue 2": {
                "first valid year": 2010,
                "url": 'https://fbref.com/en/comps/60/history/Ligue-2-Seasons',
                "finder": ["Ligue-2"],
            },
            "Serie B": {
                "first valid year": 2002,
                "url": 'https://fbref.com/en/comps/18/history/Serie-B-Seasons',
                "finder": ["Serie-B"],
            },
            ##############################################
            # Men"s domestic league - 3rd tier and lower #
            ##############################################
            #######################
            # Men"s domestic cups #
            #######################
            #########################################
            # Women"s internation club competitions #
            #########################################
            "Women Champions League": {
                "first valid year": 2015,
                "url": "https://fbref.com/en/comps/181/history/Champions-League-Seasons",
                "finder": ["Champions-League"],
            },
            ######################################
            # Women"s national team competitions #
            ######################################
            "Womens World Cup": {
                "first valid year": 1991,
                "url": "https://fbref.com/en/comps/106/history/Womens-World-Cup-Seasons",
                "finder": ["Womens-World-Cup"],
            },
            "Womens Euros": {
                "first valid year": 2001,
                "url": "https://fbref.com/en/comps/162/history/UEFA-Womens-Euro-Seasons",
                "finder": ["UEFA-Womens-Euro"],
            },
            ############################
            # Women"s domestic leagues #
            ############################
            "NWSL": {
                "first valid year": 2013,
                "url": "https://fbref.com/en/comps/182/history/NWSL-Seasons",
                "finder": ["NWSL"],
            },
            "A-League Women": {
                "first valid year": 2019,
                "url": "https://fbref.com/en/comps/196/history/A-League-Women-Seasons",
                "finder": ["A-League-Women", "W-League"],
            },
            "WSL": {
                "first valid year": 2017,
                "url": "https://fbref.com/en/comps/189/history/Womens-Super-League-Seasons",
                "finder": ["Womens-Super-League"],
            },
            "D1 Feminine": {
                "first valid year": 2018,
                "url": "https://fbref.com/en/comps/193/history/Division-1-Feminine-Seasons",
                "finder": ["Division-1-Feminine"],
            },
            "Womens Bundesliga": {
                "first valid year": 2017,
                "url": "https://fbref.com/en/comps/183/history/Frauen-Bundesliga-Seasons",
                "finder": ["Frauen-Bundesliga"],
            },
            "Womens Serie A": {
                "first valid year": 2019,
                "url": "https://fbref.com/en/comps/208/history/Serie-A-Seasons",
                "finder": ["Serie-A"],
            },
            "Liga F": {
                "first valid year": 2023,
                "url": "https://fbref.com/en/comps/230/history/Liga-F-Seasons",
                "finder": ["Liga-F"],
            },
            #########################
            # Women"s domestic cups #
            #########################
            "NWSL Challenge Cup": {
                "first valid year": 2020,
                "url": "https://fbref.com/en/comps/881/history/NWSL-Challenge-Cup-Seasons",
                "finder": ["NWSL-Challenge-Cup"],
            },
            "NWSL Fall Series": {
                "first valid year": 2020,
                "url": "https://fbref.com/en/comps/884/history/NWSL-Fall-Series-Seasons",
                "finder": ["NWSL-Fall-Series"],
            },
        },
        "Understat": {
            "EPL": {"first valid year": 2015,},
            "La Liga": {"first valid year": 2015,},
            "Bundesliga":  {"first valid year": 2015,},
            "Serie A":  {"first valid year": 2015,},
            "Ligue 1":  {"first valid year": 2015,},
            "RFPL":  {"first valid year": 2015,},
        },
        "FiveThirtyEight": {
            "EPL":  {"first valid year": 2017,},
            "La Liga":  {"first valid year": 2017,},
            "Bundesliga":  {"first valid year": 2017,},
            "Serie A":  {"first valid year": 2017,},
            "Ligue 1":  {"first valid year": 2017,},
        },
        "Capology": {
            "Bundesliga":  {"first valid year": 2014,},
            "2.Bundesliga":  {"first valid year": 2020,},
            "EPL":  {"first valid year": 2014,},
            "EFL Championship":  {"first valid year": 2014,},
            "Serie A":  {"first valid year": 2010,},
            "Serie B":  {"first valid year": 2020,},
            "La Liga":  {"first valid year": 2014,},
            "La Liga 2":  {"first valid year": 2020,},
            "Ligue 1":  {"first valid year": 2014,},
            "Ligue 2":  {"first valid year": 2020,},
            "Eredivisie":  {"first valid year": 2014,},
            "Primeira Liga":  {"first valid year": 2014,},
            "Scottish PL":  {"first valid year": 2020,},
            "Super Lig":  {"first valid year": 2014,},
            "Belgian 1st Division":  {"first valid year": 2014,},
        },
        "Transfermarkt": {
            "EPL":  {"first valid year": 1993,},
            "EFL Championship": {"first valid year": 2005,},
            "EFL1": {"first valid year": 2005,},
            "EFL2": {"first valid year": 2005,},
            "Bundesliga": {"first valid year": 1964,},
            "2.Bundesliga": {"first valid year": 1982,},
            "Serie A": {"first valid year": 1930,},
            "Serie B": {"first valid year": 1930,},
            "La Liga": {"first valid year": 1929,},
            "La Liga 2": {"first valid year": 1929,},
            "Ligue 1": {"first valid year": 1970,},
            "Ligue 2": {"first valid year": 1993,},
            "Eredivisie": {"first valid year": 1955,},
            "Scottish PL": {"first valid year": 2004,},
            "Super Lig": {"first valid year": 1960,},
            "Jupiler Pro League": {"first valid year": 1987,},
            "Liga Nos": {"first valid year": 1994,},
            "Russian Premier League": {"first valid year": 2011,},
            "Brasileirao": {"first valid year": 2001,},
            "Argentina Liga Profesional": {"first valid year": 2015,},
            "MLS": {"first valid year": 1996,},
        },
        "Oddsportal": {
            "EPL": {
                "url": "https://www.oddsportal.com/football/england/premier-league",
                "first valid year": 2004,
                "finder": "premier-league",
            },
            "EFL Championship": {
                "url": "https://www.oddsportal.com/football/england/championship",
                "first valid year": 2004,
                "finder": "championship",
            },
            "EFL League 1": {
                "url": "https://www.oddsportal.com/football/england/league-one",
                "first valid year": 2004,
                "finder": "league-one",
            },
            "EFL League 2": {
                "url": "https://www.oddsportal.com/football/england/league-two",
                "first valid year": 2004,
                "finder": "league-two",
            },
            "La Liga": {
                "url": "https://www.oddsportal.com/football/spain/laliga",
                "first valid year": 2004,
                "finder": "laliga",
            },
        },
        "Sofascore": {
            # European continental club comps
            "Champions League": {
                "id": 7,
                "seasons": {
                    "03/04": 12, "04/05": 13, "05/06": 14, "06/07": 15, 
                    "07/08": 603, "08/09": 1664, "09/10": 1825, "10/11": 2764, 
                    "11/12": 3402, "12/13": 4788, "13/14": 6359, "14/15": 8226, 
                    "15/16": 10390, "16/17": 11773, "17/18": 13415, 
                    "18/19": 17351, "19/20": 23766, "20/21": 29267, 
                    "21/22": 36886, "22/23": 41897, "23/24": 52162,
                },
            },
            "Europa League": {
                "id": 679,
                "seasons": {
                    "09/10": 2155, "10/11": 2765, "11/12": 3403, "12/13": 4790, 
                    "13/14": 6361, "14/15": 8228, "15/16": 10391, "16/17": 11774, 
                    "17/18": 13416, "18/19": 17352, "19/20": 23755, 
                    "20/21": 29343, "21/22": 37725, "22/23": 44509, 
                    "23/24": 53654,
                },
            },
            "Europa Conference League": {
                "id": 17015,
                "seasons": {
                    "21/22": 37074, "22/23": 42224, "23/24": 52327,
                },
            },
            # European domestic leagues
            "EPL": {
                "id": 17,
                "seasons": {
                    "93/94": 25680, "94/95": 29167, "95/96": 25681, 
                    "96/97": 25682, "97/98": 51, "98/99": 50, "99/00": 49, 
                    "00/01": 48, "01/02": 47, "02/03": 46, "03/04": 1, 
                    "04/05": 2, "05/06": 3, "06/07": 4, "07/08": 581, 
                    "08/09": 1544, "09/10": 2139, "10/11": 2746, "11/12": 3391,
                    "12/13": 4710, "13/14": 6311, "14/15": 8186, "15/16": 10356,
                    "16/17": 11733, "17/18": 13380, "18/19": 17359, 
                    "19/20": 23776, "20/21": 29415, "21/22": 37036, 
                    "22/23": 41886, "23/24": 52186,
                },
            },
            "La Liga": {
                "id": 8,
                "seasons": {
                    "93/94": 25687, "94/95": 25688,  "95/96": 25690, 
                    "96/97": 25689, "97/98": 75, "98/99": 74, "99/00": 73, 
                    "00/01": 72, "01/02": 71, "02/03": 70, "03/04": 99, 
                    "04/05": 100, "05/06": 101, "06/07": 102, "07/08": 669, 
                    "08/09": 1587, "09/10": 2252, "10/11": 2896, "11/12": 3502,
                    "12/13": 4959, "13/14": 6559, "14/15": 8578, "15/16": 10495,
                    "16/17": 11906, "17/18": 13662, "18/19": 18020,
                    "19/20": 24127, "20/21": 32501, "21/22": 37223, 
                    "22/23": 42409, "23/24": 52376,
                },
            },
            "Bundesliga": {
                "id": 35,
                "seasons": {
                    "92/93": 13088, "97/98": 107, "98/99": 106, "99/00": 105, 
                    "00/01": 104, "01/02": 103, "02/03": 90, "03/04": 91, 
                    "04/05": 92, "05/06": 93, "06/07": 94,  "07/08": 525, 
                    "08/09": 1557, "09/10": 2188, "10/11": 2811, "11/12": 3405,
                    "12/13": 4792, "13/14": 6303, "14/15": 8238, "15/16": 10419,
                    "16/17": 11818, "17/18": 13477, "18/19": 17597, 
                    "19/20": 23538, "20/21": 28210, "21/22": 37166, 
                    "22/23": 42268, "23/24": 52608,
                },
            },
            "Serie A": {
                "id": 23,
                "seasons": {
                    "97/98": 85, "98/99": 84, "99/00": 83, "00/01": 82, 
                    "01/02": 81, "02/03": 80, "03/04": 95, "04/05": 96, 
                    "05/06": 97, "06/07": 98, "07/08": 712, "08/09": 1552, 
                    "09/10": 2324, "10/11": 2930, "11/12": 3639, "12/13": 5145, 
                    "13/14": 6797, "14/15": 8618, "15/16": 10596, "16/17": 11966, 
                    "17/18": 13768, "18/19": 17932, "19/20": 24644, 
                    "20/21": 32523, "21/22": 37475, "22/23": 42415, 
                    "23/24": 52760,
                },
            },
            "Ligue 1": {
                "id": 34,
                "seasons": {
                    "97/98": 65, "98/99": 64, "99/00": 63, "00/01": 62, 
                    "01/02": 61, "02/03": 60, "03/04": 59, "04/05": 58, 
                    "05/06": 57, "06/07": 56, "07/08": 534, "08/09": 1542, 
                    "09/10": 2120, "10/11": 2719, "11/12": 3380, "12/13": 4616, 
                    "13/14": 6271, "14/15": 8122, "15/16": 10373, "16/17": 11648, 
                    "17/18": 13384, "18/19": 17279, "19/20": 23872, 
                    "20/21": 28222, "21/22": 37167, "22/23": 42273, 
                    "23/24": 52571,
                },
            },
            # South America
            "Argentina Liga Profesional": {
                "id": 155,
                "seasons": {
                    "08/09": 1636, "09/10": 2323, "10/11": 2887, "11/12": 3613,
                    "12/13": 5103, "13/14": 6455, "2014": 8338, "2015": 9651,
                    "2016": 11237, "16/17": 12117, "17/18": 13950, 
                    "18/19": 18113, "19/20": 24239, "2021": 37231, "2022": 41884,
                    "2023": 47647, 
                },
            },
            "Argentina Copa de la Liga Profesional": {
                "id": 13475,
                "seasons": {
                    "2019": 23108, "2020": 34618, "2021": 35486, "2022": 40377,
                    "2023": 47644,
                },
            },
            "Peru Liga 1": {
                "id": 406,
                "seasons": {
                    "2022": 40118 , "2023": 48078 , "2024": 57741,
                },
            },
            # USA
            "MLS": {},
            "USL Championship": {
                "id": 13363,
                "seasons": {
                    "2016": 11611, "2017": 12895, "2018": 16187, "2019": 22636,
                    "2020": 27058, "2021": 36157, "2022": 40364, "2023": 48258,
                },
            },
            "USL1": {
                "id": 13362,
                "seasons": {
                    "2019": 22635, "2020": 26862, "2021": 36019, "2022": 40280, 
                    "2023": 48265,
                },
            },
            "USL2": {
                "id": 13546,
                "seasons": {
                    "2019": 23299, "2021": 36421, "2022": 40556, "2023": 49265,
                },
            },
            # Men's international comps
            "World Cup": {
                "id": 16,
                "seasons": {
                    "1930": 40712, "1934": 17559, "1938": 17560, "1950": 40714,
                    "1954": 17561, "1958": 17562, "1962": 17563, "1966": 17564,
                    "1970": 17565, "1974": 17566, "1978": 17567, "1982": 17568,
                    "1986": 17569, "1990": 17570, "1994": 17571, "1998": 1151,
                    "2002": 2636, "2006": 16, "2010": 2531, "2014": 7528,
                    "2018": 15586, "2022": 41087,
                },
            },
            "Euros": {
                "id": 1,
                "seasons": {
                    "1972": 27050, "1976": 27049, "1980": 27046, "1984": 27048,
                    "1988": 27051, "1992": 27052, "1996": 27053, "2000": 358,
                    "2004": 356, "2008": 1162, "2012": 4136, "2016": 11098,
                    "2021": 26542,
                },
            },
            "Gold Cup": {
                "id": 140,
                "seasons": {
                    "2009": 2088, "2011": 3302, "2015": 10238, "2017": 13258,
                    "2019": 23156, "2021": 36683, "2023": 50492,
                },
            },
            # Women's international comps
            "Women's World Cup": {
                "id": 290,
                "seasons": {
                    "2011": 3144, "2015": 9602, "2019": 19902, "2023": 46930,
                },
            },
        },
    }

    # If all args are None then return full source comp info (used in unit tests)
    if year==None and league==None and source==None:
        return source_comp_info

    # Check source
    if type(source) != str:
        raise TypeError("Source must be a string.")
    if source not in list(source_comp_info.keys()):
        raise InvalidSourceException(source, source_comp_info)

    # Check league
    if type(league) != str:
        raise TypeError("League must be a string.")
    if league not in list(source_comp_info[source].keys()):
        raise InvalidLeagueException(league, source, source_comp_info)
    
    # Check year
    if source == "Oddsportal":
        if type(year) not in [type(None), int]:
            raise TypeError("For Oddsportal, the year must be an integer or `None` for the current season.")
        if type(year) == int and year < source_comp_info[source][league]["first valid year"]:
            raise InvalidYearException(year, league, source, source_comp_info)
    elif source == "Sofascore":
        if type(year) != str:
            raise TypeError("For Sofascore, the year must be a string.")
        if year not in source_comp_info[source][league]["seasons"].keys():
            raise InvalidYearException(year, league, source, source_comp_info)
    else:
        if type(year) != int and source != "Oddsportal":
            raise TypeError("Year must be an integer.")
        if year < source_comp_info[source][league]["first valid year"]:
            raise InvalidYearException(year, league, source_comp_info)
            
    # Some source competition info is year-dependent. Handle that here.
    if source == "Oddsportal":
        if league == "La Liga" and year is not None and year < 2017:
            source_comp_info["Oddsportal"]["La Liga"]["url"] = "https://www.oddsportal.com/football/spain/primera-division"
            source_comp_info["Oddsportal"]["La Liga"]["finder"] = "primera-division"
    
    return source_comp_info

########################################################################################################################
def get_proxy():
    ''' Gets a proxy address.

    Can be used to initialize a Selenium WebDriver to change the address of the\
    browser. Adapted from https://stackoverflow.com/questions/59409418/how-to-rotate-selenium-webrowser-ip-address.\
    Randomly chooses one proxy.
    
    Returns
    -------
    proxy : str
        In the form <IP address>:<port>
    '''
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    clear_output()
    
    try:
        driver.get('https://sslproxies.org/')
        table = driver.find_elements(By.TAG_NAME, 'table')[0]
        df = pd.read_html(table.get_attribute('outerHTML'))[0]
        df = df.iloc[np.where(~np.isnan(df['Port']))[0],:] # ignore nans

        ips = df['IP Address'].values
        ports = df['Port'].astype('int').values

        driver.quit()
        proxies = list()
        for i in range(len(ips)):
            proxies.append('{}:{}'.format(ips[i], ports[i]))
        i = random.randint(0, len(proxies)-1)
        return proxies[i]
    except Exception as e:
        driver.close()
        driver.quit()
        raise e
        
########################################################################################################################
def xpath_soup(element):
    """ Generate xpath from BeautifulSoup4 element.
    
    I shamelessly stole this from https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf.
    
    Args
    ----
    element : bs4.element.Tag or bs4.element.NavigableString
        BeautifulSoup4 element.
    Returns
    -------
    : str
        xpath as string
    Usage
    -----
    >>> import bs4
    >>> html = (
    ...     "<html><head><title>title</title></head>"
    ...     "<body><p>p <i>1</i></p><p>p <i>2</i></p></body></html>"
    ...     )
    >>> soup = bs4.BeautifulSoup(html, "html.parser")
    >>> xpath_soup(soup.html.body.p.i)
    "/html/body/p[1]/i"
    >>> import bs4
    >>> xml = "<doc><elm/><elm/></doc>"
    >>> soup = bs4.BeautifulSoup(xml, "lxml-xml")
    >>> xpath_soup(soup.doc.elm.next_sibling)
    "/doc/elm[2]"
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else "%s[%d]" % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
                )
            )
        child = parent
    components.reverse()
    return "/%s" % "/".join(components)
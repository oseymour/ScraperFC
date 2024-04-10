
class InvalidYearException(Exception):
    """ Raised when an invalid year is found
    """
    def __init__(self, year, league):
        self.year = year
        self.league = league
    def __str__(self):
        return f'{self.year} was not found as a valid year for {self.league}.'
    

class InvalidLeagueException(Exception):
    """ Raised when a league is not valid for a given scraping module.
    """
    def __init__(self, league, module):
        self.league = league
        self.module = module
    def __str__(self):
        return f'{self.league} is not a valid league for {self.module}.'
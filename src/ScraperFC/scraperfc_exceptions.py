

class InvalidYearException(Exception):
    """ Raised when an invalid year is found
    """
    def __init__(self, year, league, valid_years):
        self.year = year
        self.league = league
        self.valid_years = valid_years

    def __str__(self):
        return f'{self.year} is not a valid year for {self.league}. Valid years are' + \
            f' {self.valid_years}'
    

class InvalidLeagueException(Exception):
    """ Raised when a league is not valid for a given scraping module.
    """
    def __init__(self, league, module, valid_leagues):
        self.league = league
        self.module = module
        self.valid_leagues = valid_leagues

    def __str__(self):
        return f'{self.league} is not a valid league for {self.module}. Valid leagues are ' + \
            f'{self.valid_leagues}'
    

class NoMatchLinksException(Exception):
    """ Raised when no match links are found
    """
    def __init__(self, year, league, fixtures_url):
        super().__init__()
        self.fixtures_url = fixtures_url
        self.league = league
        self.year = year

    def __str__(self):
        return f'No match score elements found for {self.year} {self.league} at {self.fixtures_url}'


class ClubEloInvalidTeamException(Exception):
    """ Raised when an invalid team is used
    """
    def __init__(self, team):
        super().__init__()
        self.team = team

    def __str__(self):
        return f'{self.team} is an invalid team for ClubElo. Please check clubelo.com for valid' + \
            ' team names.'
    

class InvalidCurrencyException(Exception):
    """ Raised when an invalid currency is used with the Capology module.
    """
    def __init__(self):
        super().__init__()

    def __str__(self):
        return 'Currency must be one of "eur", "gbp", or "usd".'

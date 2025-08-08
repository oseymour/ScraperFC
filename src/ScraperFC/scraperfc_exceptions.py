from typing import Union, Sequence

class InvalidYearException(Exception):
    """ Raised when an invalid year is found
    """
    def __init__(self, year: Union[int, str], league: str, valid_years: Sequence) -> None:
        self.year = year
        self.league = league
        self.valid_years = valid_years

    def __str__(self) -> str:
        return f'{self.year} is not a valid year for {self.league}. Valid years are' +\
            f' {self.valid_years}.\n\nSee ' +\
            'https://scraperfc.readthedocs.io/en/latest/year_parameter.html for specifics.\n'


class InvalidLeagueException(Exception):
    """ Raised when a league is not valid for a given scraping module.
    """
    def __init__(self, league: str, module: str, valid_leagues: Sequence) -> None:
        self.league = league
        self.module = module
        self.valid_leagues = valid_leagues

    def __str__(self) -> str:
        return f'{self.league} is not a valid league for {self.module}. Valid leagues are ' + \
            f'{self.valid_leagues}'


class NoMatchLinksException(Exception):
    """ Raised when no match links are found
    """
    def __init__(self, year: Union[int, str], league: str, fixtures_url: str) -> None:
        super().__init__()
        self.fixtures_url = fixtures_url
        self.league = league
        self.year = year

    def __str__(self) -> str:
        return f'No match score elements found for {self.year} {self.league} at {self.fixtures_url}'


class ClubEloInvalidTeamException(Exception):
    """ Raised when an invalid team is used
    """
    def __init__(self, team: str) -> None:
        super().__init__()
        self.team = team

    def __str__(self) -> str:
        return f'{self.team} is an invalid team for ClubElo. Please check clubelo.com for valid' + \
            ' team names.'


class InvalidCurrencyException(Exception):
    """ Raised when an invalid currency is used with the Capology module.
    """
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return 'Currency must be one of "eur", "gbp", or "usd".'

class FBrefRateLimitException(Exception):
    """ Raised when FBref returns HTTP status 429, rate limit request
    """
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "FBref returned a 429 status, Too Many Requests. See " +\
            "https://www.sports-reference.com/bot-traffic.html for more details."

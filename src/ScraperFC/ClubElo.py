from datetime import datetime
from io import StringIO
import pandas as pd
import requests
from .scraperfc_exceptions import ClubEloInvalidTeamException
import warnings


class ClubElo:

    # ==========================================================================
    def scrape_team_on_date(self, team, date):
        """ Scrapes a team's ELO score on a given date.

        Args
        ----
        team : str
            To get the appropriate team name, go to clubelo.com and find the team you're looking 
            for. Copy and past the team's name as it appears in the URL.
        date : str
            Must be formatted as YYYY-MM-DD
        Returns
        -------
        elo : int
            ELO score of the given team on the given date
        -1 : int
            -1 if the team has no score on the given date
        """
        # Check inputs
        if type(team) is not str:
            raise TypeError('`team` must be a string.')
        if type(date) is not str:
            raise TypeError('`date` must be a string.')
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except Exception as E:
            warnings.warn(f'The date {date} is not formatted as YYYY-MM-DD.')
            raise E

        # use ClubElo API to get team data as Pandas DataFrame
        url = f'http://api.clubelo.com/{team}'
        while 1:
            try:
                r = requests.get(url)
                break
            except requests.exceptions.ConnectionError:
                pass
        df = pd.read_csv(StringIO(r.text), sep=',')
        if df.shape[0] == 0:
            raise ClubEloInvalidTeamException(team)

        # find row that given date falls in
        for i in df.index:
            from_date = datetime.strptime(df.loc[i, 'From'], '%Y-%m-%d')
            to_date = datetime.strptime(df.loc[i, 'To'], '%Y-%m-%d')
            if (date > from_date and date < to_date) or date == from_date or date == to_date:
                return df.loc[i, 'Elo']

        return -1  # return -1 if ELO not found for given date

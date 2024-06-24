from datetime import datetime
from io import StringIO
import pandas as pd
import requests
from .scraperfc_exceptions import ClubEloInvalidTeamException


class ClubElo:

    # ==============================================================================================
    def scrape_team_on_date(self, team: str, date: str) -> float:
        """ Scrapes a team's ELO score on a given date.

        Parameters
        ----------
        team : str
            To get the appropriate team name, go to clubelo.com and find the team you're looking
            for. Copy and past the team's name as it appears in the URL.
        date : str
            Must be formatted as YYYY-MM-DD
        Returns
        -------
        elo : int
            ELO score of the given team on the given date. Will be -1 if the team has no score on
            that date.
        """
        # Check inputs
        if not isinstance(team, str):
            raise TypeError('`team` must be a string.')
        if not isinstance(date, str):
            raise TypeError('`date` must be a string.')

        # Use ClubElo API to get team data as Pandas DataFrame
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
        df["From"] = pd.DatetimeIndex(df["From"])
        df["To"] = pd.DatetimeIndex(df["To"])
        date_datetime = datetime.strptime(date, '%Y-%m-%d')
        df = df.loc[(date_datetime >= df["From"]) & (date_datetime <= df["To"])]

        elo = -1 if df.shape[0] == 0 else df["Elo"].values[0]

        return elo  # return -1 if ELO not found for given date

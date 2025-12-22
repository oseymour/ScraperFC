from datetime import datetime as dt
from io import StringIO
import pandas as pd
import requests


class ClubElo:

    # ==============================================================================================
    @staticmethod
    def _clubelo_query(url: str) -> pd.DataFrame:
        """ Query ClubElo API and return as DataFrame

        :param url: ClubElo API URL to query
        :type url: str

        :rtype: pd.DataFrame
        """
        if not isinstance(url, str):
            raise TypeError("`url` must be a string.")

        r = requests.get(url)
        return pd.read_csv(StringIO(r.text))

    # ==============================================================================================
    @staticmethod
    def _is_valid_date(date: str) -> bool:
        """ Check if date is valid

        :param date: Date to check
        :type date: str

        :rtype: bool
        """
        try:
            dt.strptime(date, "%Y-%m-%d")
            return True
        except Exception:
            return False

    # ==============================================================================================
    def scrape_team(self, team: str) -> pd.DataFrame:
        """ Scrape team data

        :param team: Team name to scrape data for.
        :type team: str

        :rtype: pd.DataFrame
        """
        if not isinstance(team, str):
            raise TypeError("`team` must be a string.")

        df = self._clubelo_query(f"http://api.clubelo.com/{team}")
        if df.shape[0] == 0:
            raise Exception(f"No data for team `{team}` was found.")
        return df

    # ==============================================================================================
    def scrape_date(self, date: str) -> pd.DataFrame:
        """ Scrape ELO scores on specific date

        :param date: Date to scrape data for. Date should be in YYYY-MM-DD format.
        :type date: str

        :rtype: pd.DataFrame
        """
        if not isinstance(date, str):
            raise TypeError("`date` must be a string.")
        if not self._is_valid_date(date):
            raise ValueError(f"{date} is not a valid date. Format must be YYYY-MM-DD.")
        return self._clubelo_query(f"http://api.clubelo.com/{date}")

    # ==============================================================================================
    def scrape_fixtures(self) -> pd.DataFrame:
        """ Scrape upcoming fixtures

        See http://clubelo.com/API for more info on what kind of data is returned.

        :rtype: pd.DataFrame
        """
        return self._clubelo_query("https://api.clubelo.com/Fixtures")

    # ==============================================================================================
    def scrape_team_on_date(self, team: str, date: str) -> float:
        """ Scrape ELO score of a team on a specific date

        :param team: Team name to scrape data for.
        :type team: str
        :param date: Date to scrape data for. Date should be in YYYY-MM-DD format.
        :type date: str

        :rtype: float
        """
        if not isinstance(team, str):
            raise TypeError("`team` must be a string.")
        if not isinstance(date, str):
            raise TypeError("`date` must be a string.")
        if not self._is_valid_date(date):
            raise ValueError(f"{date} is not a valid date. Format must be YYYY-MM-DD.")

        df = self.scrape_date(date)
        team_row = df[df["Club"] == team]
        if team_row.shape[0] == 0:
            raise Exception(f"No rows for team `{team}` were found on {date}.")
        return float(team_row["Elo"].array[0])

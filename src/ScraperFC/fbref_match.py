import pandas as pd
from dataclasses import dataclass


@dataclass
class FBrefMatch():
    url: str
    date: str
    stage: str
    home_team: str
    away_team: str
    home_id: str
    away_id: str
    home_goals: str
    away_goals: str
    home_player_stats: dict[str, pd.DataFrame]
    away_player_stats: dict[str, pd.DataFrame]
    all_shots: pd.DataFrame
    home_shots: pd.DataFrame
    away_shots: pd.DataFrame
    referee: str | None
    ar1: str | None
    ar2: str | None
    fourth_official: str | None
    var: str | None

    def __repr__(self) -> str:
        return f"FBrefMatch({self.date}, `{self.url}`)"

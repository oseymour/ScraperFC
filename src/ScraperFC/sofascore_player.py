from datetime import datetime
from dataclasses import dataclass
import pandas as pd

@dataclass
class SofascorePlayer:
    id: int
    name: str
    team_name: str
    team_id: int
    position: str | None
    positions_detailed: list[str] | None
    weight: int | None
    height: int | None
    dob: datetime | None
    preferred_foot: str | None
    country: str | None
    contract_until: datetime | None
    market_value: int | None
    market_value_currency: str | None
    career_stats: pd.DataFrame

    def __repr__(self) -> str:
        return f"SofascorePlayer(id={self.id}, name={self.name})"

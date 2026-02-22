import pandas as pd
from .utils.botasaurus_getters import botasaurus_browser_get_json

# ==================================================================================================
def _get_player_career_stats_df(player_id: int, api_prefix: str) -> pd.DataFrame:
    if not isinstance(player_id, int):
        raise TypeError("player_id must be an integer.")

    response = botasaurus_browser_get_json(f"{api_prefix}/player/{player_id}/statistics")
    if "seasons" not in response:
        return pd.DataFrame()
    else:
        df = pd.DataFrame(response["seasons"])

        # Explode any columns that are dictionaries
        while dict in set(type(df.loc[0,col]) for col in df.columns):
            for col in df.columns:
                if isinstance(df.loc[0,col], dict):
                    temp = df[col].apply(pd.Series).add_prefix(f"{col}.")
                    df = df.drop(columns=[col]).join(temp)

        return df

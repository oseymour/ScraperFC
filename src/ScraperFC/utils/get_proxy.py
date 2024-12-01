import requests
from bs4 import BeautifulSoup
import random
import pandas as pd
from io import StringIO


def get_proxy() -> str:
    """ Gets a proxy address.
    
    Adapted from
    https://stackoverflow.com/questions/59409418/how-to-rotate-selenium-webrowser-ip-address.
    Randomly chooses one proxy.
    
    Parameters
    ----------
    None

    Returns
    -------
    proxy : str
        In the form <IP address>:<port>
    """
    r = requests.get("https://sslproxies.org/")
    soup = BeautifulSoup(r.content, "html.parser")
    df = pd.read_html(StringIO(str(soup.find("table"))))[0]
    df = df.loc[~df["Port"].isna(),:]
    rand_row_idx = random.randint(0, df.shape[0]-1)
    row = df.iloc[rand_row_idx,:]
    proxy = f"{row['IP Address']}:{row['Port']}"
    return proxy
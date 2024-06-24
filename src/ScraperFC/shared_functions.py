import requests
from bs4 import BeautifulSoup
import bs4
import random
import pandas as pd
from io import StringIO
from typing import Union

# ==================================================================================================
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

# ==================================================================================================
def xpath_soup(element: Union[bs4.element.Tag, bs4.element.NavigableString]) -> str:
    """ Generate xpath from BeautifulSoup4 element.
    
    I shamelessly stole this from https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf.
    
    Parameters
    ----------
    element : bs4.element.Tag or bs4.element.NavigableString
        BeautifulSoup4 element.
    
    Returns
    -------
    xpath : str
    
    Example
    -------
    >>> import bs4
    >>> html = (
    ...     "<html><head><title>title</title></head>"
    ...     "<body><p>p <i>1</i></p><p>p <i>2</i></p></body></html>"
    ... )
    >>> soup = bs4.BeautifulSoup(html, "html.parser")
    >>> xpath_soup(soup.html.body.p.i)
    "/html/body/p[1]/i"
    >>> import bs4
    >>> xml = "<doc><elm/><elm/></doc>"
    >>> soup = bs4.BeautifulSoup(xml, "lxml-xml")
    >>> xpath_soup(soup.doc.elm.next_sibling)
    "/doc/elm[2]"
    """
    components = []
    child = element if element.name else element.parent  # type: ignore
    for parent in child.parents:  # type: ignore
        siblings = parent.find_all(child.name, recursive=False)  # type: ignore
        components.append(
            child.name if 1 == len(siblings) else "%s[%d]" % (  # type: ignore
                child.name,  # type: ignore
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return "/%s" % "/".join(components)

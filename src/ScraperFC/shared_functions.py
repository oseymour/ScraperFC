from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from IPython.display import clear_output
import random
import pandas as pd
import numpy as np

# ==================================================================================================
def get_proxy():
    """ Gets a proxy address.
    
    Adapted from https://stackoverflow.com/questions/59409418/how-to-rotate-selenium-webrowser-ip-address.
    Randomly chooses one proxy.
    
    Parameters
    ----------
    None

    Returns
    -------
    proxy : str
        In the form <IP address>:<port>
    """
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    clear_output()
    
    try:
        driver.get('https://sslproxies.org/')
        table = driver.find_elements(By.TAG_NAME, 'table')[0]
        df = pd.read_html(table.get_attribute('outerHTML'))[0]
        df = df.iloc[np.where(~np.isnan(df['Port']))[0],:] # ignore nans

        ips = df['IP Address'].values
        ports = df['Port'].astype('int').values

        driver.quit()
        proxies = list()
        for i in range(len(ips)):
            proxies.append('{}:{}'.format(ips[i], ports[i]))
        i = random.randint(0, len(proxies)-1)
        return proxies[i]
    except Exception as e:
        driver.close()
        driver.quit()
        raise e
        
########################################################################################################################
def xpath_soup(element):
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
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else "%s[%d]" % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
                )
            )
        child = parent
    components.reverse()
    return "/%s" % "/".join(components)
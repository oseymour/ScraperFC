
import sys
sys.path.append("..")
import ScraperFC as sfc # import local ScraperFC
import itertools
# from ScraperFC import sources
import datetime
import numpy as np
    
########################################################################################################################
def get_random_league_seasons(source, sample_size):
    """
    """
    if source not in sfc.sources.keys():
        raise ValueError(f'Source needs to be one of {list(sfc.sources.keys())}')
    
    leagues = sfc.sources[source].keys()
    years = range(
        min([sfc.sources[source][k]['first valid year'] for k in sfc.sources[source]]) - 1, 
        datetime.datetime.now().year + 1
    )
    all_iterator = list(itertools.product(leagues, years))

    if type(sample_size) is str:
        if sample_size != 'all':
            raise ValueError('If sample_size is a string, it must be "all".')
        iter = all_iterator

    elif type(sample_size) is int:
        if sample_size <= 0:
            raise ValueError('If sample_size is an integer, it must be > 0.')
        try:
            scraper = sfc.Understat()
            iter = list()
            while len(iter) < sample_size:
                got_random = False
                while not got_random:
                    random_idx = np.random.choice(len(all_iterator), size=1, replace=False)[0]
                    league, year = np.array(all_iterator)[random_idx]
                    league, year = str(league), int(year)
                    try:
                        sfc.shared_functions.check_season(year,league,'Understat')
                        scraper.get_match_links(year, league)
                        got_random = True
                    except:
                        pass
                if (league,year) not in iter:
                    iter.append((league,year))
        finally:
            scraper.close()

    else:
        raise TypeError('sample_size must be an int > 0 or the string "all".')

    return iter
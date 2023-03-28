
import sys
sys.path.append('..')
import ScraperFC as sfc # import local ScraperFC
import itertools
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
        min([sfc.sources[source][k]['first valid year'] for k in sfc.sources[source]]), 
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
        elif sample_size > len(all_iterator):
            raise ValueError(f'Sample size too large. For source {source}, sample size must <= {len(all_iterator)}.')
        
        # Try new league and year combos until we get n=sample_size valid seasons
        iter = list()
        while len(iter) < sample_size:
            random_idx = np.random.choice(len(all_iterator), size=1, replace=False)[0]
            league, year = np.array(all_iterator)[random_idx]
            league, year = str(league), int(year)
            if year < sfc.sources[source][league]['first valid year']:
                # all_iterator spans minimum first valid year for all leagues from source
                continue
            sfc.shared_functions.check_season(year, league, source)
            if (league,year) not in iter:
                iter.append((league,year))

    else:
        raise TypeError('sample_size must be an int > 0 or the string "all".')

    return iter
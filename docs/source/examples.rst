Installation
============

Installing ScaperFC is easy! Just go ahead and run ``pip install ScraperFC`` from the command line and you should be good to go!

Examples
========

FBRef
*****

This example shows how to scrape the league table of the 2019-20 English Premier League season from FBRef.

.. code-block:: python

    import ScraperFC as sfc
    import traceback
    
    scraper = sfc.FBRef() # initialize the FBRef scraper
    try:
        # scrape the table
        lg_table = scraper.scrape_league_table(year=2020, leauge='EPL')
    except:
        """ Catch and print any exceptions. This allows us to still close 
        the scraper below, even if an exception occurs.
        """
        traceback.print_exc()
        
    """ It's important to close the scraper when you're done with it. 
    Otherwise, you'll have a bunch of webdrivers open and running in 
    the background. 
    """
    scraper.close()


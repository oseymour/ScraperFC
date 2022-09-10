Installation
============

Installing ScaperFC is easy! Just go ahead and run ``pip install ScraperFC`` from the command line and you should be good to go!

Examples
========

FBRef
*****

.. code-block:: python
    """ This example shows how to scrape the league table of the 2019-20 English Premier League season from FBRef. """
    import ScraperFC as sfc
    import traceback
    
    scraper = sfc.FBRef()
    try:
        lg_table = scraper.scrape_league_table(year=2020, leauge='EPL')
    except:
        traceback.print_exc()
        
    """ It's important to close the scraper when you're done with it. Otherwise, you'll have a bunch of webdrivers open and running in the background. """
    scraper.close()


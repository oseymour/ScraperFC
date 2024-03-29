==============
FBRef Examples
==============

************
League table
************

This example shows how to scrape the league table of the 2019-20 English 
Premier League season from FBRef.

.. code-block:: python

    import ScraperFC as sfc
    import traceback
    
    # Initialize the FBRef scraper
    scraper = sfc.FBRef() 
    try:
        # Scrape the table
        lg_table = scraper.scrape_league_table(year=2020, league='EPL')
    except:
        # Catch and print any exceptions. This allows us to still close the 
        # scraper below, even if an exception occurs.
        traceback.print_exc()
    finally:
        # It's important to close the scraper when you're done with it. Otherwise, 
        # you'll have a bunch of webdrivers open and running in the background. 
        scraper.close()

And here is the output.

.. image:: ./images/fbref_league_table_example.png

----------

***********
Match stats
***********

In this code block, we're scraping data from an FBRef match page. The example 
I've chosen is So'ton 2:5 Tottenham from 20 Sept, 2020.

.. code-block:: python

    import ScraperFC as sfc
    import traceback
    
    # Initialize the FBRef scraper
    scraper = sfc.FBRef() 
    try:
        # Scrape the match using the FBRef match link
        link = 'https://fbref.com/en/matches/967efd56/Southampton-Tottenham-Hotspur-September-20-2020-Premier-League'
        match = scraper.scrape_match(link=link)
    except:
        # Catch and print any exceptions.
        traceback.print_exc()
    finally:
        # Again, make sure to close the scraper when you're done
        scraper.close()

The output of ``scrape_match()`` can be a little confusing, but it contains a
lot of information. There are 3 columns that are Pandas Series of Pandas 
DataFrames. These are ``Home Player Stats``, ``Away Player Stats``, and 
``Shots``.

Home/Away Player Stats
----------------------
These Series can be accessed by calling 
``match['Home Player Stats'].values[0]`` in a cell following the example above.
The DataFrames that are part of this Series can be then be called. 
``match['Home Player Stats'].values[0]['Summary']`` would return this 
DataFrame in this example.

.. image:: ./images/fbref_match_home_player_summary.png

The home/away player stats that are available for each match will depend on the
competition and year of the match. Not all matches will have xG, for example.
To see which DataFrames are available, run 
``match['Home Player Stats'].values[0].keys()`` or 
``match['Away Player Stats'].values[0].keys()``.

Shots
-----
The Shots Series is similar to the Home/Away Player Stats Series. `If` there is
shot data available for a match on FBRef, this Series will contain 3 DataFrames,
``Both``, ``Home``, ``Away``. In the case where a home or away team doesn't have
a shot in the match, they won't have a DataFrame in this Series.

An example of a shot DataFrame is here.

.. image:: ./images/fbref_match_shots_both.png

----------

********************
Player Scout Reports
********************

COMING SOON

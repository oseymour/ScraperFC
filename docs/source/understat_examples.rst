==================
Understat Examples
==================

************
League table
************

Similar to FBRef you can scrape the league table from Understat. The code below scrapes the 2022/23 La Liga table.

.. code-block:: python

    import ScraperFC as sfc
    import traceback
    
    # Initialize the Understat scraper
    scraper = sfc.Understat() 
    try:
        # Scrape the table
        lg_table = scraper.scrape_league_table(year=2023, league="La Liga")
    except:
        # Catch and print any exceptions. This allows us to still close the 
        # scraper below, even if an exception occurs.
        traceback.print_exc()
    finally:
        # It"s important to close the scraper when you"re done with it. Otherwise, 
        # you"ll have a bunch of webdrivers open and running in the background. 
        scraper.close()

The league table from Understat has a lot more advanced metrics than the one from FBRef, however. The screenshot below
was taken from code run on 14 Nov 2022.

.. image:: ./images/understat_league_table_example.png

**************************
Shot XY Locations and Data
**************************

One really valuable dataset on Understat is their shot location data, and other data associated with the shot. The code
below scrapes the shot maps of all matches from the 2022/23 La Liga season.

.. code-block:: python

    import ScraperFC as sfc
    import traceback
    
    # Initialize the Understat scraper
    scraper = sfc.Understat() 
    try:
        # Scrape the table
        lg_table = scraper.scrape_shot_xy(year=2023, league="La Liga")
    except:
        # Catch and print any exceptions. This allows us to still close the 
        # scraper below, even if an exception occurs.
        traceback.print_exc()
    finally:
        # It"s important to close the scraper when you"re done with it. Otherwise, 
        # you"ll have a bunch of webdrivers open and running in the background. 
        scraper.close()

This function returns a dict. The keys are Understat match ID"s, the values for each match is another dict. This second
dict contains 2 lists, one for all of the home team shots and another for all of the away team shots. See the example 
below, which summarizes data scraped a match between Barcelona and Athletic Club (match ID 19065). ::

    shots = {
        "19065": 
            "h": [
                {
                    "id": "495925",
                    "minute": "11",
                    "result": "SavedShot",
                    "X": "0.8019999694824219",
                    "Y": "0.3240000152587891",
                    "xG": "0.026046590879559517",
                    "player": "Ousmane Dembélé",
                    "h_a": "h",
                    "player_id": "3226",
                    "situation": "OpenPlay",
                    "season": "2022",
                    "shotType": "LeftFoot",
                    "match_id": "19065",
                    "h_team": "Barcelona",
                    "a_team": "Athletic Club",
                    "h_goals": "4",
                    "a_goals": "0",
                    "date": "2022-10-23 19:00:00",
                    "player_assisted": "Pedri",
                    "lastAction": "Pass"
                }, 
                # more home shots
            ],
            "a": [
                {
                    "id": "495930",
                    "minute": "40",
                    "result": "BlockedShot",
                    "X": "0.759000015258789",
                    "Y": "0.5059999847412109",
                    "xG": "0.026612039655447006",
                    "player": "Iñaki Williams",
                    "h_a": "a",
                    "player_id": "2399",
                    "situation": "OpenPlay",
                    "season": "2022",
                    "shotType": "RightFoot",
                    "match_id": "19065",
                    "h_team": "Barcelona",
                    "a_team": "Athletic Club",
                    "h_goals": "4",
                    "a_goals": "0",
                    "date": "2022-10-23 19:00:00",
                    "player_assisted": "Nico Williams",
                    "lastAction": "BallTouch"
                },
                # more away shots
            ],
        },
        # more matches
    }

*************
Attack Speeds
*************

COMING SOON

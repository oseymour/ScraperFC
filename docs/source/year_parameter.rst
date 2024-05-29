====================
The `year` Parameter
====================

Starting in ScraperFC v3.0, the `year` parameter is slightly different for each module. This page
details what the parameter needs to be and how to find valid options for the modules that use this 
argument.

Regardless of module, if you enter an invalid year argument, the InvalidYearException will be raised
and the error printout should show a list of valid years.

.. _capology_year:

Capology
--------
- Type: `str`
- Format: "2023-24". This should match the values in the year dropdown for the league on the
  Capology website.
- `get_valid_seasons()`: Will return a list of strings of the valid seasons for the chosen league.

.. _fbref_year:

FBref
-----
- Type: `str`
- Format: This should match the years as seen on the "Competition History" page of the league on 
  the FBref website.
- `get_valid_seasons()`: Will return a dict with valid years as the keys.

.. _fivethirtyeight_year:

FiveThirtyEight
---------------
- Type: `int`
- Format: Calendar year that the season begins in (e.g. 2022 for the 2022/23 season).
- There is no `get_valid_seasons()` for this module.

.. _sofascore_year:

Sofascore
---------
- Type: `str`
- Format: Needs to match the values in the year dropdown for the league on the Sofascore website.
- `get_valid_seasons()`: Will return a dict with the valid season strings as the keys.

.. _transfermarkt_year:

Transfermarkt
-------------
- Type: `str`
- Format: Needs to match the values in the year dropdown for the league on the Transfermarkt website.
- `get_valid_seasons()`: Returns a list with the valid seasons.

.. _understat_year:

Understat
---------
- Type: `str`
- Format: "2023-2024", see the values in the year dropdown on the Understat website.
- `get_valid_seasons()`: Returns a list with the valid seasons.

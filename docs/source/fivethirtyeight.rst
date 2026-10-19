===============
FiveThirtyEight
===============

The FiveThirtyEight module has been deprecated because there are easier ways to scrape the
FiveThirtyEight data than the ScraperFC code I wrote.

They put links to their CSV data on one of their GitHub pages,
https://github.com/fivethirtyeight/data/tree/master/soccer-spi, and these can be loaded into Python
really easily using the Pandas :code:`read_csv()` function.

For example, the scrape all of their historical club matches you can do:

.. code-block:: python

   import pandas as pd
   df = pd.read_csv("https://projects.fivethirtyeight.com/soccer-api/club/spi_matches.csv")

.. note::
   Following ABC News's shutdown of FiveThirtyEight, the ``projects.fivethirtyeight.com/soccer-api/club/spi_matches.csv`` URL now redirects to ``abcnews.com/politics`` (and the GitHub archive is frozen at June 2023). For an active, daily-updated replacement providing club attack/defence ratings, Dixon–Coles match probabilities, and 10,000-simulation league projections across 93 leagues via a free keyless JSON API and CC-BY-4.0 dataset, see `Football Charts <https://www.football-charts.com/developers>`_.

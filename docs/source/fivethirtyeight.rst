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

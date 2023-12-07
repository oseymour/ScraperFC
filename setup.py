import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
    
setuptools.setup(
    name = "ScraperFC",
    version = "2.9.2",
    author = "Owen Seymour",
    author_email = "osmour043@gmail.com",
    description = "Package for scraping soccer data from a variety of sources.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/oseymour/ScraperFC",
    packages = ["ScraperFC",],
    keywords = [
        "soccer", "football", "Premier League", "Serie A", "La Liga", 
        "Bundesliga", "Ligue 1", "web scraping", "soccer data", 
        "soccer stats", "football data", "football stats",
        "web scraping soccer stats", "web scraping football stats",
        "web scraping soccer data", "web scraping football data", "fbref", 
        "understat", "transfermarkt", "538", "fivethirtyeight", "capology", 
        "clubelo", "oddsportal",
    ],
    install_requires = [
        "selenium", "pandas", "numpy", "datetime", "ipython", "requests", "bs4", 
        "lxml", "tqdm",
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    python_requires = ">=3.6"
)
  
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath("../../src/"))


# -- Project information ---------------------------------------------------------------------------
project = "ScraperFC"
copyright = "2022, Owen Seymour"
author = "Owen Seymour"


# -- General configuration -------------------------------------------------------------------------
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "myst_nb"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["*.ipynb_checkpoints"]

# Ignore warnings for some types not being found
nitpick_ignore = [
    ("py:class", "pandas.DataFrame"), ("py:class", "optional"),
    ("py:class", "default True"), ("py:class", "default False"), ("py:class", "bs4.element.Tag"),
    ("py:class", "bs4.element.NavigableString"), ("py:class", "dicts"),
    ("py:class", "pandas.core.frame.DataFrame"),
    ("py:class", "botasaurus_requests.request_class.Request"),
    ("py:class", "botasaurus_requests.response.Response"),
    ("py:class", "botasaurus.request.Request"),
    ("py:class", "botasaurus.browser.Driver"),
    ("py:class", "botasaurus_driver.driver.Driver"),
]

# Validate numpy docstring formatting
numpydoc_validation_checks = {"all"}

# HTML theme
html_theme = "furo"

# myst-nb config options
nb_execution_mode = "off"

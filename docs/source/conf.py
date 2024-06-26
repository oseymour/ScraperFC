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
sys.path.insert(0, os.path.abspath('../../src/'))


# -- Project information -----------------------------------------------------

project = 'ScraperFC'
copyright = '2022, Owen Seymour'
author = 'Owen Seymour'
# release = '2.1.2'  # The full version, including alpha/beta/rc tags


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon',]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['*.ipynb_checkpoints']

# Ignore warnings for some types not being found
nitpick_ignore = [
    ('py:class', 'DataFrame'), ('py:class', 'DataFrames'), ('py:class', 'optional'),
    ('py:class', 'default True'), ('py:class', 'default False'), ('py:class', 'bs4.element.Tag'),
    ('py:class', 'bs4.element.NavigableString'), ('py:class', 'dicts'), 
    ("py:class", "pandas.core.frame.DataFrame")
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
# html_theme = 'sphinx_rtd_theme'
# html_theme = 'pydata_sphinx_theme'
html_theme = "furo"

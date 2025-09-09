# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
#sys.path.insert(0, os.path.abspath('../../')) # 20250908WF - dont care about flywheel code for now :)
sys.path.insert(0, os.path.abspath('../../examples'))


project = 'file-curator'
copyright = '2025, Will Foran, Elijah Hudlow'
author = 'Will Foran, Elijah Hudlow'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 
              'sphinx.ext.napoleon', # Supports Google/NumPy-style docstrings 
              'sphinx.ext.viewcode', # Adds [source] links to the docs
              'sphinx.ext.autosummary'
              ]
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "docs", ".venv", "lib"]


autodoc_mock_imports = ["flywheel_gear_toolkit", "pydicom", "nibabel", "toml", "flywheel"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

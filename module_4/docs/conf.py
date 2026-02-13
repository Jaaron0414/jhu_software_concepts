"""Sphinx configuration for Grad Cafe Analytics documentation."""

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Grad Cafe Analytics'
author = 'Jie Xu'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build']

html_theme = 'sphinx_rtd_theme'
html_static_path = []

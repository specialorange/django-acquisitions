# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(".."))

# Configure Django settings before importing any Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

# Try to setup Django, but don't fail if models have issues
try:
    import django
    django.setup()
except Exception:
    # Mock Django modules for autodoc if setup fails
    pass

# -- Project information -----------------------------------------------------
project = "django-acquisitions"
copyright = "2024, specialorange"
author = "specialorange"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]

# Create _static directory if it doesn't exist (for custom CSS/JS)
os.makedirs(os.path.join(os.path.dirname(__file__), "_static"), exist_ok=True)

# -- Extension configuration -------------------------------------------------

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/5.2/", "https://docs.djangoproject.com/en/5.2/_objects/"),
}

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# Mock imports for autodoc when Django isn't fully available
autodoc_mock_imports = ["django", "celery", "twilio", "rest_framework"]

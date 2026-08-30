"""
src/config.py

Central place that loads API keys and settings from the .env file.
Every other script in src/ imports from here instead of calling
load_dotenv() and os.environ[...] repeatedly.
"""

import os
from dotenv import load_dotenv

# Reads the .env file in the project root and loads its values
# into the environment for this Python process.
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
BHL_API_KEY = os.environ["BHL_API_KEY"]
GBIF_API_BASE = os.environ.get("GBIF_API_BASE", "https://api.gbif.org/v1")
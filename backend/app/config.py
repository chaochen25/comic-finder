"""
Loads configuration from environment variables and allows for change settings without changing code
"""
import os
from dotenv import load_dotenv

# reads .env file if present
load_dotenv() 

# For this MVP we use a local SQLite file. Later we could switch to Postgres by changing this.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./comics.db")

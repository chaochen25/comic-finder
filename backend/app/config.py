import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = (Path(__file__).resolve().parents[1] / ".env")
load_dotenv(dotenv_path=ENV_PATH, override=False)

DATABASE_URL       = os.getenv("DATABASE_URL", "sqlite:///./comics.db")
MARVEL_PUBLIC_KEY  = os.getenv("MARVEL_PUBLIC_KEY")
MARVEL_PRIVATE_KEY = os.getenv("MARVEL_PRIVATE_KEY")
MARVEL_BASE_URL    = os.getenv("MARVEL_BASE_URL", "https://gateway.marvel.com/v1/public")

COMICVINE_API_KEY  = os.getenv("COMICVINE_API_KEY")
COMICVINE_BASE_URL = os.getenv("COMICVINE_BASE_URL", "https://comicvine.gamespot.com/api")

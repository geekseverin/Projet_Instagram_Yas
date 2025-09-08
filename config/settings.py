# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()  # charge le .env à la racine

INSTAGRAM_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("IG_BUSINESS_ID")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "insta_etl")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")

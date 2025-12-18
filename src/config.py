import os

from dotenv import load_dotenv

load_dotenv()

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
SIDEBAR_WIDTH = 64
SIDEBAR_RATIO = 1
CONTENT_RATIO = 18
STYLESHEET_PATH = "src/ui/styles.qss"

DATABASE_URL = "sqlite:///mathtermind.db"
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

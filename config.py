import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_PATH = DATA_DIR / "mathtermind.db"

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
SIDEBAR_WIDTH = 64
SIDEBAR_RATIO = 1
CONTENT_RATIO = 18
STYLESHEET_PATH = "src/ui/styles.qss"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY")

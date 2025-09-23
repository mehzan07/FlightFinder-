import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set in the environment")
    return value

# === Local Development Settings ===
FLASK_APP = get_env_var("FLASK_APP")
FLASK_ENV = get_env_var("FLASK_ENV")
PORT = int(get_env_var("PORT"))
IS_LOCAL = get_env_var("IS_LOCAL").lower() == "true"
DEBUG_MODE = get_env_var("DEBUG_MODE").lower() == "true"

# === Feature Flags ===
FEATURED_FLIGHT_LIMIT = int(get_env_var("FEATURED_FLIGHT_LIMIT"))

# === Travelpayouts API Credentials ===
API_TOKEN = get_env_var("API_TOKEN")
AFFILIATE_MARKER = get_env_var("AFFILIATE_MARKER")
HOST = get_env_var("HOST")
USER_IP = get_env_var("USER_IP")
USE_REAL_API = get_env_var("USE_REAL_API").lower() == "true"
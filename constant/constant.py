import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file using absolute path
script_dir = Path(__file__).parent.parent.absolute()
env_path = script_dir / ".env"
load_dotenv(env_path)

# Google Ads API Configuration
SCOPES = ['https://www.googleapis.com/auth/adwords']
API_VERSION = "v19"
BASE_URL = f"https://googleads.googleapis.com/{API_VERSION}"

# Environment Variables
GOOGLE_ADS_CREDENTIALS_PATH = os.environ.get("GOOGLE_ADS_CREDENTIALS_PATH")
GOOGLE_ADS_DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")

# API Endpoints
ENDPOINTS = {
    'LIST_CUSTOMERS': f"{BASE_URL}/customers:listAccessibleCustomers",
    'SEARCH': f"{BASE_URL}/customers/{{customer_id}}/googleAds:search",
    'SEARCH_STREAM': f"{BASE_URL}/customers/{{customer_id}}/googleAds:searchStream",
    'KEYWORD_IDEAS': f"{BASE_URL}/customers/{{customer_id}}:generateKeywordIdeas"
}

# Default Values
DEFAULT_PAGE_SIZE = 25
DEFAULT_GEO_TARGET = 'geoTargetConstants/2840'  # United States
DEFAULT_LANGUAGE = 'languageConstants/1000'  # English
DEFAULT_NETWORK = 'GOOGLE_SEARCH_AND_PARTNERS'

# Valid Months for Keyword Planner
VALID_MONTHS = [
    'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'
] 
from fastmcp import FastMCP
from typing import Any, Dict, List, Optional, Union
import os
import json
import requests
from datetime import datetime, timedelta
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load from .env file if it exists
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.warning("python-dotenv not installed, skipping .env file loading")

# Import organized modules
from constant import GOOGLE_ADS_DEVELOPER_TOKEN
# Direct token management - no auth folder needed
import uuid
import time
import asyncio
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('google_ads_server')

mcp = FastMCP("Google Ads Tools 🚀")


class SimpleTokenManager:
    """Simple token manager that stores tokens in credentials.json in code directory."""
    
    def __init__(self):
        # Use absolute paths to ensure files are found regardless of working directory
        script_dir = Path(__file__).parent.absolute()
        self.credentials_file = script_dir / "credentials.json"
        self.base_url = "https://reimagine-dev.gomarble.ai/api/authorise/google"
        self.key = "google"
        
        # Find client secret file - support multiple naming patterns
        self.client_secret_file = self._find_client_secret_file(script_dir)
    
    def _find_client_secret_file(self, script_dir: Path) -> Path:
        """Find client secret file with flexible naming patterns."""
        # Try different naming patterns in order of preference
        patterns = [
            "client_secret.json",  # Standard name
            "client_secret_*.json",  # Google's default download format
            "*client_secret*.json"  # Any file containing client_secret
        ]
        
        for pattern in patterns:
            matches = list(script_dir.glob(pattern))
            if matches:
                # Return the first match
                logger.info(f"Found client secret file: {matches[0].name}")
                return matches[0]
        
        # If no file found, return the standard name (will be used for error messages)
        return script_dir / "client_secret.json"
        
    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from local credentials.json file."""
        if not self.credentials_file.exists():
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _load_client_secret(self) -> Dict[str, Any]:
        """Load client secret from any client_secret*.json file."""
        if not self.client_secret_file.exists():
            raise FileNotFoundError(
                f"Client secret file not found. Please download your OAuth 2.0 Client ID "
                f"credentials from Google Cloud Console and save as 'client_secret.json' "
                f"(or keep the original filename like 'client_secret_xxxxx.apps.googleusercontent.com.json')"
            )
        
        try:
            with open(self.client_secret_file, 'r') as f:
                data = json.load(f)
                # Handle both formats: direct client info or nested in 'web' or 'installed'
                if 'web' in data:
                    return data['web']
                elif 'installed' in data:
                    return data['installed']
                else:
                    return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise Exception(f"Error reading {self.client_secret_file.name}: {e}")

    def _save_credentials(self, credentials: Dict[str, Any]) -> None:
        """Save credentials to local credentials.json file."""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            logger.info(f"Credentials saved to {self.credentials_file}")
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def _open_url(self, url: str) -> None:
        """Open URL in default browser."""
        try:
            webbrowser.open(url)
            logger.info(f"Opened browser to: {url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
            logger.info(f"Please manually open: {url}")
    
    async def _generate_access_token(self, credentials: Dict[str, Any]) -> str:
        """Generate new access token via web OAuth flow (like TypeScript version)."""
        try:
            # Use the same web-based OAuth flow as the TypeScript version
            base_url = "https://reimagine-dev.gomarble.ai/api/authorise/google"
            request_id = str(uuid.uuid4())
            auth_start_url = f"{base_url}/start?request_id={request_id}"
            token_fetch_url = f"{base_url}/get-token?request_id={request_id}"
            
            logger.info("Starting web-based OAuth flow...")
            logger.info(f"Opening browser to: {auth_start_url}")
            self._open_url(auth_start_url)
            
            # Poll for token completion (same as TypeScript version)
            max_attempts = 6  # 1 minute (10-second intervals)
            
            for attempt in range(max_attempts):
                try:
                    # Wait 10 seconds between attempts
                    await asyncio.sleep(10)
                    
                    logger.info(f"Checking for token completion (attempt {attempt + 1}/{max_attempts})...")
                    
                    response = requests.get(token_fetch_url, timeout=15)
                    
                    if response.status_code != 200:
                        continue
                    
                    data = response.json()
                    
                    if data.get("status") == "pending":
                        logger.info("Authentication still pending...")
                        continue
                    
                    if data.get("status") == "error":
                        raise Exception(f"OAuth error: {data.get('message', 'Unknown error')}")
                    
                    if data.get("status") == "success":
                        logger.info("OAuth flow completed successfully!")
                        
                        # Store all token data (same as TypeScript version)
                        for data_key, data_value in data.items():
                            if data_key != "status":
                                credentials[f"{self.key}_{data_key}"] = data_value
                        
                        self._save_credentials(credentials)
                        return data.get("access_token")
                        
                except Exception as e:
                    logger.error(f"Error during token generation: {e}")
                    raise
            
            raise Exception(f"Timeout: Authentication did not complete within {max_attempts * 10} seconds")
            
        except Exception as e:
            logger.error(f"Error during token generation: {e}")
            raise
    
    async def _refresh_access_token(self, credentials: Dict[str, Any], refresh_token: str) -> str:
        """Refresh access token using web endpoint (like TypeScript version)."""
        try:
            base_url = "https://reimagine-dev.gomarble.ai/api/authorise/google"
            refresh_url = f"{base_url}/refresh-token?refresh_token={refresh_token}"
            
            logger.info("Refreshing access token...")
            
            response = requests.get(refresh_url, timeout=15)
            
            if response.status_code != 200:
                raise Exception(f"Refresh failed with status {response.status_code}")
            
            data = response.json()
            
            if data.get("status") == "success":
                logger.info("Token refreshed successfully!")
                
                # Update stored credentials (same as TypeScript version)
                for data_key, data_value in data.items():
                    if data_key != "status":
                        credentials[f"{self.key}_{data_key}"] = data_value
                
                self._save_credentials(credentials)
                return data.get("access_token")
            else:
                raise Exception(f"Refresh error: {data.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise
    
    def _is_token_expired(self, credentials: Dict[str, Any]) -> bool:
        """Check if the current token is expired."""
        expires_at = credentials.get(f"{self.key}_expires_at")
        if not expires_at:
            return True
        
        # Add 5 minute buffer before expiration
        buffer_time = 5 * 60  # 5 minutes in seconds
        return time.time() >= (expires_at - buffer_time)
    
    def get_stored_credentials(self) -> Dict[str, Any]:
        """Get all stored credentials."""
        return self._load_credentials()
    
    def clear_credentials(self) -> None:
        """Clear all stored credentials."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
            logger.info("Credentials cleared")
    
    def get_oauth_info(self) -> Dict[str, str]:
        """Get OAuth configuration information."""
        info = {
            "base_url": self.base_url,
            "start_endpoint": f"{self.base_url}/start",
            "token_endpoint": f"{self.base_url}/get-token",
            "refresh_endpoint": f"{self.base_url}/refresh-token",
            "scope": "https://www.googleapis.com/auth/adwords",
            "flow_type": "web_based_oauth"
        }
        
        # Add client secret info if available (for testing/debugging)
        try:
            client_secret = self._load_client_secret()
            info["client_secret_file"] = self.client_secret_file.name
            info["client_id"] = client_secret.get('client_id', 'Not found')[:20] + "..." if client_secret.get('client_id') else 'Not found'
            info["has_client_secret"] = True
        except:
            info["client_secret_file"] = "Not found"
            info["has_client_secret"] = False
        
        return info


# Initialize simple token manager
token_manager = SimpleTokenManager()


# Server startup
logger.info("🚀 Starting Google Ads MCP Server...")
logger.info("✅ Server ready! Use token management tools for authentication.")


def format_customer_id(customer_id: str) -> str:
    """Format customer ID by removing dashes."""
    return customer_id.replace("-", "")

@mcp.tool
def run_gaql(
    customer_id: str,
    query: str,
    google_access_token: str,
    manager_id: str = ""
) -> Dict[str, Any]:
    """Execute GAQL using the non-streaming search endpoint for consistent JSON parsing."""
    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")

    formatted_customer_id = format_customer_id(customer_id)
    url = (
        f"https://googleads.googleapis.com/v19/customers/"
        f"{formatted_customer_id}/googleAds:search"
    )
    headers = {
        'Authorization': f'Bearer {google_access_token}',
        'developer-token': GOOGLE_ADS_DEVELOPER_TOKEN,
        'Content-Type': 'application/json',
    }
    if manager_id:
        headers['login-customer-id'] = format_customer_id(manager_id)

    payload = {'query': query}
    resp = requests.post(url, headers=headers, json=payload)
    if not resp.ok:
        raise Exception(
            f"Error executing GAQL: {resp.status_code} {resp.reason} - {resp.text}"
        )
    data = resp.json()
    results = data.get('results', [])
    return {
        'results': results,
        'query': query,
        'totalRows': len(results),
    }

def execute_gaql(
    customer_id: str,
    query: str,
    google_access_token: str,
    manager_id: str = ""
) -> Dict[str, Any]:
    """Execute GAQL using the non-streaming search endpoint for consistent JSON parsing."""
    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")

    formatted_customer_id = format_customer_id(customer_id)
    url = (
        f"https://googleads.googleapis.com/v19/customers/"
        f"{formatted_customer_id}/googleAds:search"
    )
    headers = {
        'Authorization': f'Bearer {google_access_token}',
        'developer-token': GOOGLE_ADS_DEVELOPER_TOKEN,
        'Content-Type': 'application/json',
    }
    if manager_id:
        headers['login-customer-id'] = format_customer_id(manager_id)

    payload = {'query': query}
    resp = requests.post(url, headers=headers, json=payload)
    if not resp.ok:
        raise Exception(
            f"Error executing GAQL: {resp.status_code} {resp.reason} - {resp.text}"
        )
    data = resp.json()
    results = data.get('results', [])
    return {
        'results': results,
        'query': query,
        'totalRows': len(results),
    }

def get_customer_name(
    customer_id: str,
    google_access_token: str
) -> str:
    """Retrieve descriptive_name for the given customer ID."""
    try:
        query = "SELECT customer.descriptive_name FROM customer"
        result = execute_gaql(customer_id, query, google_access_token)
        rows = result.get('results', [])
        if not rows:
            return "Name not available (no results)"
        customer = rows[0].get('customer', {})
        return customer.get('descriptiveName', "Name not available (missing field)")
    except Exception:
        return "Name not available (error)"


def is_manager_account(
    customer_id: str,
    google_access_token: str
) -> bool:
    """Check if a customer account is a manager (MCC)."""
    try:
        query = "SELECT customer.manager FROM customer"
        result = execute_gaql(customer_id, query, google_access_token)
        rows = result.get('results', [])
        if not rows:
            return False
        return bool(rows[0].get('customer', {}).get('manager', False))
    except Exception:
        return False


def get_sub_accounts(
    manager_id: str,
    google_access_token: str
) -> List[Dict[str, Any]]:
    """List sub-accounts under a manager account."""
    try:
        query = (
            "SELECT customer_client.id, customer_client.descriptive_name, "
            "customer_client.level, customer_client.manager "
            "FROM customer_client WHERE customer_client.level > 0"
        )
        result = execute_gaql(manager_id, query, google_access_token)
        rows = result.get('results', [])
        subs = []
        for row in rows:
            client = row.get('customerClient', {}) or row.get('customer_client', {})
            cid = format_customer_id(str(client.get('id', '')))
            subs.append({
                'id': cid,
                'name': client.get('descriptiveName', f"Sub-account {cid}"),
                'access_type': 'managed',
                'is_manager': bool(client.get('manager', False)),
                'parent_id': manager_id,
                'level': int(client.get('level', 0))
            })
        return subs
    except Exception:
        return []

@mcp.tool
def list_accounts(
    google_access_token: str
) -> Dict[str, Any]:
    """List all accessible accounts including nested sub-accounts."""
    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")

    # Fetch top-level accessible customers
    url = "https://googleads.googleapis.com/v19/customers:listAccessibleCustomers"
    headers = {
        'Authorization': f'Bearer {google_access_token}',
        'developer-token': GOOGLE_ADS_DEVELOPER_TOKEN,
        'Content-Type': 'application/json',
    }
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        raise Exception(
            f"Error listing accounts: {resp.status_code} {resp.reason} - {resp.text}"
        )
    data = resp.json()
    resource_names = data.get('resourceNames', [])
    if not resource_names:
        return {'accounts': [], 'message': 'No accessible accounts found.'}

    accounts = []
    seen = set()
    for resource in resource_names:
        cid = resource.split('/')[-1]
        fid = format_customer_id(cid)
        name = get_customer_name(fid, google_access_token)
        manager = is_manager_account(fid, google_access_token)
        account = {
            'id': fid,
            'name': name,
            'access_type': 'direct',
            'is_manager': manager,
            'level': 0
        }
        accounts.append(account)
        seen.add(fid)
        # Include sub-accounts (and nested)
        if manager:
            subs = get_sub_accounts(fid, google_access_token)
            for sub in subs:
                if sub['id'] not in seen:
                    accounts.append(sub)
                    seen.add(sub['id'])
                    # nested level
                    if sub['is_manager']:
                        nested = get_sub_accounts(sub['id'], google_access_token)
                        for n in nested:
                            if n['id'] not in seen:
                                accounts.append(n)
                                seen.add(n['id'])

    return {
        'accounts': accounts,
        'total_accounts': len(accounts)
    }


@mcp.tool
def run_keyword_planner(
    customer_id: str,
    keywords: List[str],
    google_access_token: str,
    manager_id: str,
    page_url: Optional[str] = None,
    start_year: Optional[int] = None,
    start_month: Optional[str] = None,
    end_year: Optional[int] = None,
    end_month: Optional[str] = None
) -> Dict[str, Any]:
    """Generate keyword ideas using Google Ads KeywordPlanIdeaService.

    This tool allows you to generate keyword ideas based on seed keywords or a page URL. 
    You can specify targeting parameters such as language, location, and network to refine your keyword suggestions.

    Args:
        customer_id: The Google Ads customer ID (10 digits, no dashes)
        keywords: A list of seed keywords to generate ideas from
        google_access_token: OAuth access token for Google Ads API
        manager_id: Manager ID if access type is 'managed'
        page_url: Optional page URL related to your business to generate ideas from
        start_year: Optional start year for historical data (defaults to previous year)
        start_month: Optional start month for historical data (defaults to JANUARY)
        end_year: Optional end year for historical data (defaults to current year)
        end_month: Optional end month for historical data (defaults to current month)

    Returns:
        A list of keyword ideas with associated metrics

    Note:
        - At least one of 'keywords' or 'page_url' must be provided
        - Ensure that the 'customer_id' is formatted as a string, even if it appears numeric
        - Valid months: JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY, AUGUST, SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER
    """
    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")
    
    # Validate that at least one of keywords or page_url is provided
    if (not keywords or len(keywords) == 0) and not page_url:
        raise ValueError("At least one of keywords or page URL is required, but neither was specified.")
    
    formatted_customer_id = format_customer_id(customer_id)
    url = f"https://googleads.googleapis.com/v19/customers/{formatted_customer_id}:generateKeywordIdeas"
    
    headers = {
        'Authorization': f'Bearer {google_access_token}',
        'developer-token': GOOGLE_ADS_DEVELOPER_TOKEN,
        'Content-Type': 'application/json',
    }
    
    if manager_id:
        headers['login-customer-id'] = format_customer_id(manager_id)
    
    # Set up dynamic date range with user-provided values or smart defaults
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.strftime('%B').upper()
    
    valid_months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
    
    # Use provided dates or fall back to defaults
    start_year_final = start_year or (current_year - 1)
    start_month_final = start_month.upper() if start_month and start_month.upper() in valid_months else 'JANUARY'
    end_year_final = end_year or current_year
    end_month_final = end_month.upper() if end_month and end_month.upper() in valid_months else current_month
    
    # Build the request body according to Google Ads API specification
    request_body = {
        # Use proper resource name format for language (English)
        'language': 'languageConstants/1000',
        # Use proper resource name format for geo targeting (United States as default)
        'geoTargetConstants': ['geoTargetConstants/2840'],
        # Set network to Google Search and Partners
        'keywordPlanNetwork': 'GOOGLE_SEARCH_AND_PARTNERS',
        # Include adult keywords setting
        'includeAdultKeywords': False,
        # Limit results for analysis
        'pageSize': 25,
        # Add historical metrics with dynamic or user-specified date range
        'historicalMetricsOptions': {
            'yearMonthRange': {
                'start': {
                    'year': start_year_final,
                    'month': start_month_final
                },
                'end': {
                    'year': end_year_final,
                    'month': end_month_final
                }
            }
        }
    }
    
    # Set the appropriate seed based on what's provided
    if (not keywords or len(keywords) == 0) and page_url:
        # Only page URL was specified, so use a UrlSeed
        request_body['urlSeed'] = {'url': page_url}
    elif keywords and len(keywords) > 0 and not page_url:
        # Only keywords were specified, so use a KeywordSeed
        request_body['keywordSeed'] = {'keywords': keywords}
    elif keywords and len(keywords) > 0 and page_url:
        # Both page URL and keywords were specified, so use a KeywordAndUrlSeed
        request_body['keywordAndUrlSeed'] = {
            'url': page_url,
            'keywords': keywords
        }
    
    try:
        response = requests.post(url, headers=headers, json=request_body)
        
        if not response.ok:
            error_text = response.text
            raise Exception(f"Error executing request: {response.status_code} {response.reason} - {error_text}")
        
        results = response.json()
        
        if 'results' not in results or not results['results']:
            return {
                "message": f"No keyword ideas found for the provided inputs.\n\nKeywords: {', '.join(keywords) if keywords else 'None'}\nPage URL: {page_url or 'None'}\nAccount: {formatted_customer_id}",
                "keywords": keywords or [],
                "page_url": page_url,
                "date_range": f"{start_month_final} {start_year_final} to {end_month_final} {end_year_final}"
            }
        
        # Format the results for better readability
        formatted_results = []
        for result in results['results']:
            keyword_idea = result.get('keywordIdeaMetrics', {})
            keyword_text = result.get('text', 'N/A')
            
            formatted_result = {
                'keyword': keyword_text,
                'avg_monthly_searches': keyword_idea.get('avgMonthlySearches', 'N/A'),
                'competition': keyword_idea.get('competition', 'N/A'),
                'competition_index': keyword_idea.get('competitionIndex', 'N/A'),
                'low_top_of_page_bid_micros': keyword_idea.get('lowTopOfPageBidMicros', 'N/A'),
                'high_top_of_page_bid_micros': keyword_idea.get('highTopOfPageBidMicros', 'N/A')
            }
            formatted_results.append(formatted_result)
        
        return {
            "keyword_ideas": formatted_results,
            "total_ideas": len(formatted_results),
            "input_keywords": keywords or [],
            "input_page_url": page_url,
            "date_range": f"{start_month_final} {start_year_final} to {end_month_final} {end_year_final}"
        }
        
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def check_google_ads_token_status() -> Dict[str, Any]:
    """Check the status of stored Google Ads access token and refresh token in the code directory.
    
    This tool checks if tokens exist locally and their expiration status.
    It does NOT generate or refresh tokens, only reports their current state.
    
    Returns:
        Dictionary containing token status information
    """
    try:
        credentials = token_manager.get_stored_credentials()
        
        if not credentials:
            return {
                "status": "no_tokens",
                "message": "No access token or refresh token found in code directory",
                "has_access_token": False,
                "has_refresh_token": False,
                "is_expired": None,
                "action_needed": "Use generate_google_ads_token to create new tokens"
            }
        
        access_token = credentials.get(f"{token_manager.key}_access_token")
        refresh_token = credentials.get(f"{token_manager.key}_refresh_token")
        expires_at = credentials.get(f"{token_manager.key}_expires_at")
        
        is_expired = token_manager._is_token_expired(credentials) if expires_at else True
        
        return {
            "status": "tokens_found",
            "has_access_token": bool(access_token),
            "has_refresh_token": bool(refresh_token),
            "is_expired": is_expired,
            "expires_at": expires_at,
            "message": f"Access token: {'✅ Present' if access_token else '❌ Missing'}, "
                      f"Refresh token: {'✅ Present' if refresh_token else '❌ Missing'}, "
                      f"Status: {'🔴 Expired' if is_expired else '🟢 Valid'}",
            "action_needed": "Use refresh_google_ads_token if expired, or generate_google_ads_token if tokens missing"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool
async def generate_google_ads_token() -> Dict[str, Any]:
    """Generate new Google Ads access token and refresh token using OAuth flow.
    
    This tool starts a new OAuth flow to generate fresh tokens:
    - Opens browser to OAuth consent screen
    - Uses /start and /get-token endpoints
    - Saves new access token and refresh token to code directory
    - Use this when no tokens exist or when refresh token has also expired
    
    Args:
        
    Returns:
        Dictionary containing the new access token and status
    """
    try:
        credentials = token_manager._load_credentials()
        access_token = await token_manager._generate_access_token(credentials)
        
        return {
            "status": "success",
            "access_token": access_token,
            "message": "New access token and refresh token generated successfully",
            "action": "oauth_flow_completed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate new token: {str(e)}",
            "action": "oauth_flow_failed"
        }


@mcp.tool
async def refresh_google_ads_token() -> Dict[str, Any]:
    """Refresh Google Ads access token using existing refresh token.
    
    This tool attempts to refresh the access token using the stored refresh token.
    If refresh token is expired or invalid, it will indicate that a new token generation is needed.
        
    Returns:
        Dictionary containing refreshed access token or error with next steps
    """
    try:
        credentials = token_manager._load_credentials()
        refresh_token = credentials.get(f"{token_manager.key}_refresh_token")
        
        if not refresh_token:
            return {
                "status": "error",
                "message": "No refresh token found in code directory",
                "action_needed": "Use generate_google_ads_token to create new tokens",
                "reason": "missing_refresh_token"
            }
        
        try:
            access_token = await token_manager._refresh_access_token(credentials, refresh_token)
            return {
                "status": "success",
                "access_token": access_token,
                "message": "Access token refreshed successfully using refresh token",
                "action": "token_refreshed"
            }
        except Exception as refresh_error:
            return {
                "status": "error",
                "message": f"Refresh token failed: {str(refresh_error)}. The refresh token may be expired or invalid.",
                "action_needed": "Use generate_google_ads_token to create new access token and refresh token",
                "reason": "refresh_token_expired_or_invalid",
                "original_error": str(refresh_error)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during token refresh: {str(e)}",
            "action_needed": "Use generate_google_ads_token to create new tokens"
        }


@mcp.tool
def get_google_ads_oauth_info() -> Dict[str, Any]:
    """Get OAuth configuration information for Google Ads authentication.
    
    This tool returns the web-based OAuth configuration and endpoints.
    Use generate_google_ads_token to start the OAuth flow.
        
    Returns:
        Dictionary containing OAuth configuration information
    """
    try:
        oauth_info = token_manager.get_oauth_info()
        
        return {
            "oauth_config": oauth_info,
            "message": "Web-based OAuth configuration loaded successfully. Use generate_google_ads_token to start authentication.",
            "flow_description": {
                "1": "Browser opens to OAuth consent screen automatically",
                "2": "Complete authorization in browser",
                "3": "Tokens are automatically retrieved and saved",
                "4": "No manual code entry required"
            },
            "endpoints": {
                "start": oauth_info["start_endpoint"],
                "get_token": oauth_info["token_endpoint"],
                "refresh": oauth_info["refresh_endpoint"]
            }
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def ensure_google_ads_token() -> Dict[str, Any]:
    """Ensure valid Google Ads token exists - check, create, or overwrite as needed.
    
    This tool intelligently manages tokens:
    - If no tokens exist: Creates new tokens via OAuth flow
    - If tokens exist but expired: Attempts refresh, creates new if refresh fails
    - If tokens are corrupted/invalid: Overwrites with new tokens
    - Always ensures you have a working access token at the end
        
    Returns:
        Dictionary containing the valid access token and what action was taken
    """
    try:
        credentials = token_manager._load_credentials()
        
        # Check if no tokens exist
        if not credentials:
            return {
                "status": "no_tokens_found",
                "message": "No tokens found in code directory, creating new tokens...",
                "action": "creating_new_tokens",
                "access_token": await token_manager._generate_access_token(credentials)
            }
        
        access_token = credentials.get(f"{token_manager.key}_access_token")
        refresh_token = credentials.get(f"{token_manager.key}_refresh_token")
        
        # Check if tokens are missing
        if not access_token:
            return {
                "status": "missing_access_token",
                "message": "Access token missing, creating new tokens...",
                "action": "creating_new_tokens",
                "access_token": await token_manager._generate_access_token(credentials)
            }
        
        # Check if token is expired
        is_expired = token_manager._is_token_expired(credentials)
        
        if not is_expired:
            return {
                "status": "token_valid",
                "message": "Valid access token found, no action needed",
                "action": "using_existing_token",
                "access_token": access_token
            }
        
        # Token is expired, try to refresh
        if refresh_token:
            try:
                refreshed_token = await token_manager._refresh_access_token(credentials, refresh_token)
                return {
                    "status": "token_refreshed",
                    "message": "Access token was expired, successfully refreshed using refresh token",
                    "action": "refreshed_token",
                    "access_token": refreshed_token
                }
            except Exception as refresh_error:
                # Refresh failed, create new tokens
                return {
                    "status": "refresh_failed_creating_new",
                    "message": f"Refresh failed ({str(refresh_error)}), creating new tokens...",
                    "action": "refresh_failed_creating_new",
                    "refresh_error": str(refresh_error),
                    "access_token": await token_manager._generate_access_token(credentials)
                }
        else:
            # No refresh token, create new tokens
            return {
                "status": "no_refresh_token_creating_new",
                "message": "No refresh token found, creating new tokens...",
                "action": "creating_new_tokens",
                "access_token": await token_manager._generate_access_token(credentials)
            }
            
    except Exception as e:
        # If anything goes wrong, try to create new tokens
        try:
            credentials = {}
            new_token = await token_manager._generate_access_token(credentials)
            return {
                "status": "error_recovered",
                "message": f"Error occurred ({str(e)}), but successfully created new tokens",
                "action": "error_recovery_new_tokens",
                "original_error": str(e),
                "access_token": new_token
            }
        except Exception as final_error:
            return {
                "status": "error",
                "message": f"Failed to ensure token: {str(final_error)}",
                "original_error": str(e),
                "action": "failed"
            }

@mcp.resource("gaql://reference")
def gaql_reference() -> str:
    """Google Ads Query Language (GAQL) reference documentation."""
    return """                   Schema Format:    
                    ## Basic Query Structure
                        '''
                        SELECT field1, field2, ... 
                        FROM resource_type
                        WHERE condition
                        ORDER BY field [ASC|DESC]
                        LIMIT n
                        '''

                    ## Common Field Types
                        
                        ### Resource Fields
                        - campaign.id, campaign.name, campaign.status
                        - ad_group.id, ad_group.name, ad_group.status
                        - ad_group_ad.ad.id, ad_group_ad.ad.final_urls
                        - ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type (for keyword_view)
                        
                    ### Metric Fields
                        - metrics.impressions
                        - metrics.clicks
                        - metrics.cost_micros
                        - metrics.conversions
                        - metrics.conversions_value (direct conversion revenue - primary revenue metric)
                        - metrics.ctr
                        - metrics.average_cpc
                        
                    ### Segment Fields
                        - segments.date
                        - segments.device
                        - segments.day_of_week
                        
                        ## Common WHERE Clauses
                        
                    ### Date Ranges
                        - WHERE segments.date DURING LAST_7_DAYS
                        - WHERE segments.date DURING LAST_30_DAYS
                        - WHERE segments.date BETWEEN '2023-01-01' AND '2023-01-31'
                        
                    ### Filtering
                        - WHERE campaign.status = 'ENABLED'
                        - WHERE metrics.clicks > 100
                        - WHERE campaign.name LIKE '%Brand%'
                        - Use LIKE '%keyword%' instead of CONTAINS 'keyword' (CONTAINS not supported)

                    EXAMPLE QUERIES:

                    1. Basic campaign metrics:
                        SELECT 
                        campaign.id,
                        campaign.name, 
                        metrics.clicks, 
                        metrics.impressions,
                        metrics.cost_micros
                        FROM campaign 
                        WHERE segments.date DURING LAST_7_DAYS

                    2. Ad group performance:
                        SELECT 
                        campaign.id,
                        ad_group.name, 
                        metrics.conversions, 
                        metrics.cost_micros,
                        campaign.name
                        FROM ad_group 
                        WHERE metrics.clicks > 100

                    3. Keyword analysis (CORRECT field names):
                        SELECT 
                        campaign.id,
                        ad_group_criterion.keyword.text, 
                        ad_group_criterion.keyword.match_type,
                        metrics.average_position, 
                        metrics.ctr
                        FROM keyword_view 
                        WHERE segments.date DURING LAST_30_DAYS
                        ORDER BY metrics.impressions DESC
                        
                    4. Get conversion data with revenue:
                        SELECT
                        campaign.id,
                        campaign.name,
                        metrics.conversions,
                        metrics.conversions_value,
                        metrics.all_conversions_value,
                        metrics.cost_micros
                        FROM campaign
                        WHERE segments.date DURING LAST_30_DAYS

                    5. Search Term Insights for specific campaign:
                        SELECT
                        campaign.id,
                        campaign.name,
                        campaign_search_term_insight.category_label,
                        metrics.clicks,
                        metrics.impressions,
                        metrics.conversions,
                        metrics.cost_micros
                        FROM campaign_search_term_insight
                        WHERE campaign_search_term_insight.campaign_id = 'CAMPAIGN_ID_HERE'
                        AND segments.date DURING LAST_30_DAYS
                        ORDER BY metrics.impressions DESC
                        LIMIT 50

                    6. Campaign budget information (CORRECT approach):
                        SELECT
                        campaign.id,
                        campaign.name,
                        campaign_budget.amount_micros
                        FROM campaign_budget
                        WHERE campaign.id IN ('CAMPAIGN_ID_1', 'CAMPAIGN_ID_2')

                    IMPORTANT NOTES & COMMON ERRORS TO AVOID:

                    ### Field Errors to Avoid:
                    WRONG: campaign.campaign_budget.amount_micros
                    CORRECT: campaign_budget.amount_micros (query from campaign_budget resource)

                    WRONG: keyword.text, keyword.match_type  
                    CORRECT: ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type

                    ### Required Fields:
                    - Always include campaign.id when querying ad_group, keyword_view, or other campaign-related resources
                    - Some resources require specific reference fields in SELECT clause

                    ### Revenue Metrics:
                    - metrics.conversions_value = Direct conversion revenue (use for ROI calculations)
                    - metrics.all_conversions_value = Total attributed revenue (includes view-through)

                    ### String Matching:
                    - Use LIKE '%keyword%' not CONTAINS 'keyword'
                    - GAQL does not support CONTAINS operator

                    NOTE:
                    - Date ranges must be finite: LAST_7_DAYS, LAST_30_DAYS, or BETWEEN dates
                    - Cannot use open-ended ranges like >= '2023-01-31'
                    - Always include campaign.id when error messages request it."""

if __name__ == "__main__":
    mcp.run() 
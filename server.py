#!/usr/bin/env python3
import os
import sys
import json
import time
from typing import List, Optional, Dict, Any

# --- MCP framework (supports either official SDK or FastMCP package) ---
try:
    from mcp.server.fastmcp import FastMCP  # official MCP Python SDK
except Exception:  # pragma: no cover
    try:
        from fastmcp import FastMCP  # third-party package, same api surface for our use
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "Install the MCP SDK with `pip install mcp` (or `pip install fastmcp`)."
        ) from e

# --- Google OAuth ---
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

# ----------------------------
# Configuration & Environment
# ----------------------------
SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "google-ads-mcp")
API_BASE = os.environ.get("GOOGLE_ADS_API_BASE", "https://googleads.googleapis.com")
API_VERSION = os.environ.get("GOOGLE_ADS_API_VERSION", "v21")  # recent stable as of 2025
DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()

# Paths to secrets mounted as files in Cloud Run
CLIENT_SECRET_PATH = os.environ.get("GOOGLE_ADS_OAUTH_CONFIG_PATH", "/secrets/client_secret.json")
TOKEN_JSON_PATH = os.environ.get("GOOGLE_ADS_TOKEN_PATH", "/secrets/google_ads_token.json")

# Optional: where to save refreshed token (writable path). If not set, we best-effort write to CWD.
TOKEN_SAVE_PATH = os.environ.get("GOOGLE_ADS_TOKEN_SAVE_PATH", "./google_ads_token.json")

# Basic validation
if not DEVELOPER_TOKEN:
    print("ERROR: GOOGLE_ADS_DEVELOPER_TOKEN env var is required.", file=sys.stderr)

mcp = FastMCP(SERVER_NAME)

# ------------------------------------------------
# Helpers: OAuth, headers, simple REST wrappers
# ------------------------------------------------
SCOPE = "https://www.googleapis.com/auth/adwords"  # Google Ads API scope

def _load_client_secret() -> Dict[str, Any]:
    """Load OAuth client (desktop/web) JSON."""
    with open(CLIENT_SECRET_PATH, "r") as f:
        data = json.load(f)
    # Google’s file is usually under 'installed' or 'web'
    if "installed" in data:
        cfg = data["installed"]
    elif "web" in data:
        cfg = data["web"]
    else:
        # raw client json format
        cfg = data
    client_id = cfg.get("client_id")
    client_secret = cfg.get("client_secret")
    token_uri = cfg.get("token_uri", "https://oauth2.googleapis.com/token")
    if not client_id or not client_secret:
        raise RuntimeError("client_id/client_secret missing in client_secret.json")
    return {"client_id": client_id, "client_secret": client_secret, "token_uri": token_uri}

def _load_refresh_token_json() -> Dict[str, Any]:
    with open(TOKEN_JSON_PATH, "r") as f:
        return json.load(f)

def _get_access_token() -> str:
    """
    Build Credentials from client secret + refresh token. Refresh if needed.
    Return a valid access_token string.
    """
    client = _load_client_secret()
    token_info = _load_refresh_token_json()

    refresh_token = token_info.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("refresh_token not found in GOOGLE_ADS_TOKEN_JSON")

    creds = Credentials(
        token=None,  # let the library fetch a fresh access token
        refresh_token=refresh_token,
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=[SCOPE],
    )
    request = GoogleAuthRequest()
    creds.refresh(request)  # guarantees creds.token is valid

    # Best-effort: persist the latest token/expiry to a writable path.
    try:
        persist = {
            "refresh_token": refresh_token,
            "token_uri": client["token_uri"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "scopes": [SCOPE],
            "token": creds.token,
            "expiry": getattr(creds, "expiry", None).isoformat() if getattr(creds, "expiry", None) else None,
        }
        with open(TOKEN_SAVE_PATH, "w") as f:
            json.dump(persist, f)
    except Exception:
        # It's okay if we can't write (e.g., read-only FS). We can still operate in-memory.
        pass

    return creds.token

def _ads_headers(access_token: str, login_customer_id: Optional[str] = None) -> Dict[str, str]:
    """
    Build Google Ads REST headers.
    - developer-token is required.
    - login-customer-id is optional (use if accessing via a manager account).
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": DEVELOPER_TOKEN,
        "Content-Type": "application/json",
    }
    if login_customer_id:
        headers["login-customer-id"] = login_customer_id.replace("-", "")
    return headers

def _rest_get(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None) -> Any:
    r = requests.get(url, headers=headers, params=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"GET {url} failed: {r.status_code} {r.text}")
    return r.json()

def _rest_post(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Any:
    r = requests.post(url, headers=headers, json=body, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"POST {url} failed: {r.status_code} {r.text}")
    return r.json()

# -------------------------
# MCP Tools (Google Ads)
# -------------------------

@mcp.tool()
def list_accounts(login_customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Google Ads accounts directly accessible by the authenticated user.

    Returns a list of:
      { "customer_id": "1234567890", "resource_name": "customers/1234567890", "descriptive_name": "...", "manager": true/false }
    """
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")

    access_token = _get_access_token()
    headers = _ads_headers(access_token, login_customer_id)

    url = f"{API_BASE}/{API_VERSION}/customers:listAccessibleCustomers"
    data = _rest_get(url, headers)

    resource_names = data.get("resourceNames", [])
    results: List[Dict[str, Any]] = []

    # For each account, try to enrich with name/manager via GAQL.
    for rn in resource_names:
        # rn is like "customers/1234567890"
        customer_id = rn.split("/")[-1]

        try:
            q = "SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone, customer.manager FROM customer"
            gaql_url = f"{API_BASE}/{API_VERSION}/customers/{customer_id}/googleAds:search"
            gaql_resp = _rest_post(gaql_url, headers, {"query": q, "pageSize": 1})
            descriptive_name = None
            manager = None
            if "results" in gaql_resp and gaql_resp["results"]:
                row = gaql_resp["results"][0]
                cust = row.get("customer", {})
                descriptive_name = cust.get("descriptiveName") or cust.get("descriptive_name")
                manager = cust.get("manager")
            results.append(
                {
                    "customer_id": customer_id,
                    "resource_name": rn,
                    "descriptive_name": descriptive_name,
                    "manager": manager,
                }
            )
        except Exception:
            # If GAQL enrich fails (permissions, etc.), still return the ID.
            results.append({"customer_id": customer_id, "resource_name": rn})

    return results


@mcp.tool()
def run_gaql(
    customer_id: str,
    query: str,
    login_customer_id: Optional[str] = None,
    page_size: int = 1000,
    max_pages: int = 10,
) -> Dict[str, Any]:
    """
    Execute a GAQL query against a specific customer account.

    Args:
      customer_id: e.g., "1234567890" (no dashes)
      query: GAQL string, e.g., "SELECT campaign.id, metrics.impressions FROM campaign WHERE segments.date DURING LAST_7_DAYS"
      login_customer_id: optional manager account to act through
      page_size: up to 10,000 (Google Ads search uses pagination)
      max_pages: safety cap to avoid runaway pagination

    Returns JSON with 'results' (combined across pages) and 'summary' metadata.
    """
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")
    if not customer_id or not query:
        raise RuntimeError("customer_id and query are required")

    access_token = _get_access_token()
    headers = _ads_headers(access_token, login_customer_id)

    url = f"{API_BASE}/{API_VERSION}/customers/{customer_id}/googleAds:search"
    all_results: List[Dict[str, Any]] = []
    page_token = None
    pages = 0

    while pages < max_pages:
        body = {"query": query, "pageSize": page_size}
        if page_token:
            body["pageToken"] = page_token

        resp = _rest_post(url, headers, body)
        all_results.extend(resp.get("results", []))
        page_token = resp.get("nextPageToken")
        pages += 1
        if not page_token:
            break

    return {
        "customer_id": customer_id,
        "result_count": len(all_results),
        "results": all_results,
        "pages": pages,
    }


@mcp.tool()
def run_keyword_planner(
    customer_id: str,
    keywords: List[str],
    language_id: str = "1000",  # 1000 = English
    geo_target_constants: Optional[List[str]] = None,  # e.g., ["2840"] for US
    page_url: Optional[str] = None,
    login_customer_id: Optional[str] = None,
    include_adult: bool = False,
) -> Dict[str, Any]:
    """
    Generate keyword ideas (KeywordPlanIdeaService.generateKeywordIdeas).

    Args:
      customer_id: Google Ads customer ID where Keyword Planner is invoked.
      keywords: seed keywords.
      language_id: numeric ID (e.g., "1000" for English).
      geo_target_constants: list of numeric geo IDs (e.g., ["2840"] for United States).
      page_url: optional URL seed.
      login_customer_id: optional manager account to act through.
      include_adult: include adult keywords.

    Returns a simplified list of {text, avgMonthlySearches, competition, lowTopOfPageBidMicros, highTopOfPageBidMicros}
    """
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")
    if not customer_id or not keywords:
        raise RuntimeError("customer_id and keywords are required")

    access_token = _get_access_token()
    headers = _ads_headers(access_token, login_customer_id)

    # REST path: POST /vXX/customers:generateKeywordIdeas
    url = f"{API_BASE}/{API_VERSION}/customers:generateKeywordIdeas"

    body: Dict[str, Any] = {
        "customerId": customer_id,
        "language": f"languageConstants/{language_id}",
        "includeAdultKeywords": include_adult,
    }

    if geo_target_constants:
        body["geoTargetConstants"] = [f"geoTargetConstants/{g}" for g in geo_target_constants]

    # Use keywordSeed and/or urlSeed per docs.
    if keywords:
        body["keywordSeed"] = {"keywords": keywords}
    if page_url:
        body["urlSeed"] = {"url": page_url}

    resp = _rest_post(url, headers, body)
    ideas = []
    for item in resp.get("results", []):
        txt = item.get("text")
        metrics = item.get("keywordIdeaMetrics", {})
        ideas.append(
            {
                "text": txt,
                "avgMonthlySearches": metrics.get("avgMonthlySearches"),
                "competition": metrics.get("competition"),
                "lowTopOfPageBidMicros": metrics.get("lowTopOfPageBidMicros"),
                "highTopOfPageBidMicros": metrics.get("highTopOfPageBidMicros"),
            }
        )

    return {"customer_id": customer_id, "count": len(ideas), "ideas": ideas}


# ---------------------------------------
# Entrypoint: Streamable HTTP `/mcp`
# ---------------------------------------
if __name__ == "__main__":
    # Cloud Run contract: listen on 0.0.0.0:$PORT
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))

    # Run a single-path MCP endpoint at /mcp (Agent‑Builder expects this shape).
    # See MCP SDK docs for Streamable HTTP servers. 
    # (If you ever mount behind a base path, keep exact `/mcp` to avoid /mcp vs /mcp/ 404s.)
    mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")

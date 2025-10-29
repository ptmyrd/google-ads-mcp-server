#!/usr/bin/env python3
# Google Ads MCP server (Streamable HTTP) for Cloud Run

import os, sys, json
from typing import List, Optional, Dict, Any

# Official MCP SDK
from mcp.server.fastmcp import FastMCP

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "google-ads-mcp")
API_BASE = os.environ.get("GOOGLE_ADS_API_BASE", "https://googleads.googleapis.com")
API_VERSION = os.environ.get("GOOGLE_ADS_API_VERSION", "v22")
DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()

# These point to the files created by your **volume mounts**
CLIENT_SECRET_PATH = os.environ.get("GOOGLE_ADS_OAUTH_CONFIG_PATH", "/secrets_client/CLIENT_SECRET_JSON")
TOKEN_JSON_PATH    = os.environ.get("GOOGLE_ADS_TOKEN_PATH",        "/secrets_token/GOOGLE_ADS_TOKEN_JSON")

TOKEN_SAVE_PATH = os.environ.get("GOOGLE_ADS_TOKEN_SAVE_PATH", "./google_ads_token.json")
SCOPE = "https://www.googleapis.com/auth/adwords"

if not DEVELOPER_TOKEN:
    print("ERROR: Missing env var GOOGLE_ADS_DEVELOPER_TOKEN", file=sys.stderr)

def _load_client_secret() -> Dict[str, Any]:
    with open(CLIENT_SECRET_PATH, "r") as f:
        data = json.load(f)
    if "installed" in data:
        cfg = data["installed"]
    elif "web" in data:
        cfg = data["web"]
    else:
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
    client = _load_client_secret()
    token_info = _load_refresh_token_json()
    refresh_token = token_info.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("refresh_token not found in GOOGLE_ADS_TOKEN_JSON")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=[SCOPE],
    )
    creds.refresh(GoogleAuthRequest())

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
        pass

    return creds.token

def _ads_headers(access_token: str, login_customer_id: Optional[str] = None) -> Dict[str, str]:
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

mcp = FastMCP(SERVER_NAME)

@mcp.tool()
def list_accounts(login_customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")
    headers = _ads_headers(_get_access_token(), login_customer_id)
    data = _rest_get(f"{API_BASE}/{API_VERSION}/customers:listAccessibleCustomers", headers)
    out: List[Dict[str, Any]] = []
    for rn in data.get("resourceNames", []):
        cid = rn.split("/")[-1]
        try:
            q = ("SELECT customer.id, customer.descriptive_name, "
                 "customer.currency_code, customer.time_zone, customer.manager FROM customer")
            gaql_url = f"{API_BASE}/{API_VERSION}/customers/{cid}/googleAds:search"
            resp = _rest_post(gaql_url, headers, {"query": q, "pageSize": 1})
            name, mgr = None, None
            if resp.get("results"):
                cust = resp["results"][0].get("customer", {})
                name = cust.get("descriptiveName") or cust.get("descriptive_name")
                mgr  = cust.get("manager")
            out.append({"customer_id": cid, "resource_name": rn, "descriptive_name": name, "manager": mgr})
        except Exception:
            out.append({"customer_id": cid, "resource_name": rn})
    return out

@mcp.tool()
def run_gaql(customer_id: str, query: str, login_customer_id: Optional[str] = None,
             page_size: int = 1000, max_pages: int = 10) -> Dict[str, Any]:
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")
    if not customer_id or not query:
        raise RuntimeError("customer_id and query are required")
    headers = _ads_headers(_get_access_token(), login_customer_id)
    url = f"{API_BASE}/{API_VERSION}/customers/{customer_id}/googleAds:search"
    all_results, page_token, pages = [], None, 0
    while pages < max_pages:
        body = {"query": query, "pageSize": page_size}
        if page_token: body["pageToken"] = page_token
        resp = _rest_post(url, headers, body)
        all_results += resp.get("results", [])
        page_token = resp.get("nextPageToken")
        pages += 1
        if not page_token: break
    return {"customer_id": customer_id, "result_count": len(all_results), "results": all_results, "pages": pages}

@mcp.tool()
def run_keyword_planner(customer_id: str, keywords: List[str], language_id: str = "1000",
                        geo_target_constants: Optional[List[str]] = None, page_url: Optional[str] = None,
                        login_customer_id: Optional[str] = None, include_adult: bool = False,
                        keyword_plan_network: str = "GOOGLE_SEARCH_AND_PARTNERS") -> Dict[str, Any]:
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")
    if not customer_id or not keywords:
        raise RuntimeError("customer_id and keywords are required")
    headers = _ads_headers(_get_access_token(), login_customer_id)
    url = f"{API_BASE}/{API_VERSION}/customers:generateKeywordIdeas"
    body: Dict[str, Any] = {
        "customerId": customer_id,
        "language": f"languageConstants/{language_id}",
        "includeAdultKeywords": include_adult,
        "keywordPlanNetwork": keyword_plan_network,
    }
    if geo_target_constants:
        body["geoTargetConstants"] = [f"geoTargetConstants/{g}" for g in geo_target_constants]
    if keywords:
        body["keywordSeed"] = {"keywords": keywords}
    if page_url:
        body["urlSeed"] = {"url": page_url}
    resp = _rest_post(url, headers, body)
    ideas = []
    for item in resp.get("results", []):
        m = item.get("keywordIdeaMetrics", {})
        ideas.append({
            "text": item.get("text"),
            "avgMonthlySearches": m.get("avgMonthlySearches"),
            "competition": m.get("competition"),
            "lowTopOfPageBidMicros": m.get("lowTopOfPageBidMicros"),
            "highTopOfPageBidMicros": m.get("highTopOfPageBidMicros"),
        })
    return {"customer_id": customer_id, "count": len(ideas), "ideas": ideas}

# Build the ASGI app; uvicorn will serve it on 0.0.0.0:$PORT
app = mcp.streamable_http_app()

#!/usr/bin/env python3
"""
Google Ads MCP server (Streamable HTTP) for Cloud Run.

- Exposes an MCP endpoint at /mcp using the official MCP Python SDK.
- Uses user-based OAuth (refresh token) to call Google Ads REST endpoints.
- Binds to 0.0.0.0:$PORT (Cloud Run requirement).
"""

import os
import sys
import json
from typing import List, Optional, Dict, Any

# MCP SDK (official)
from mcp.server.fastmcp import FastMCP

# ASGI server
import uvicorn

# HTTP and OAuth
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

# ----------------------------
# Configuration (env + secrets)
# ----------------------------
SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "google-ads-mcp")
API_BASE = os.environ.get("GOOGLE_ADS_API_BASE", "https://googleads.googleapis.com")
API_VERSION = os.environ.get("GOOGLE_ADS_API_VERSION", "v22")  # latest as of Oct 2025; override if needed.  # noqa: E501
DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()

# Mounted secrets (Cloud Run → Variables & Secrets → mount as files)
CLIENT_SECRET_PATH = os.environ.get("GOOGLE_ADS_OAUTH_CONFIG_PATH", "/secrets/client_secret.json")
TOKEN_JSON_PATH = os.environ.get("GOOGLE_ADS_TOKEN_PATH", "/secrets/google_ads_token.json")

# Optional writable path to persist refreshed access tokens (best‑effort)
TOKEN_SAVE_PATH = os.environ.get("GOOGLE_ADS_TOKEN_SAVE_PATH", "./google_ads_token.json")

SCOPE = "https://www.googleapis.com/auth/adwords"

# Basic guardrails early, so failures are loud & clear in logs
if not DEVELOPER_TOKEN:
    print("ERROR: Missing env var GOOGLE_ADS_DEVELOPER_TOKEN", file=sys.stderr)


# ----------------------------
# Helper functions
# ----------------------------
def _load_client_secret() -> Dict[str, Any]:
    """Load OAuth client (desktop/web) JSON; normalize fields."""
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
    """
    Build Credentials from client secret + refresh token. Refresh on demand and return access_token.
    """
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
    request = GoogleAuthRequest()
    creds.refresh(request)

    # Best‑effort persistence to a writable file (secrets are read‑only)
    try:
        persist = {
            "refresh_token": refresh_token,
            "token_uri": client["token_uri"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "scopes": [SCOPE],
            "token": creds.token,
            "expiry": getattr(creds, "expiry", None).isoformat() if getattr(creds, "expiry", None) else None,  # noqa: E501
        }
        with open(TOKEN_SAVE_PATH, "w") as f:
            json.dump(persist, f)
    except Exception:
        pass

    return creds.token


def _ads_headers(access_token: str, login_customer_id: Optional[str] = None) -> Dict[str, str]:
    """Google Ads REST headers (developer-token required; optional login-customer-id)."""
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


# ----------------------------
# MCP server + tools
# ----------------------------
mcp = FastMCP(SERVER_NAME)

@mcp.tool()
def list_accounts(login_customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Google Ads accounts accessible to the authenticated user.
    Returns items like:
    {
      "customer_id": "1234567890",
      "resource_name": "customers/1234567890",
      "descriptive_name": "...",
      "manager": true/false
    }
    """
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")

    access_token = _get_access_token()
    headers = _ads_headers(access_token, login_customer_id)

    # customers:listAccessibleCustomers (GET; no customerId path)  # Docs: REST overview + sample
    url = f"{API_BASE}/{API_VERSION}/customers:listAccessibleCustomers"
    data = _rest_get(url, headers)

    resource_names = data.get("resourceNames", [])
    out: List[Dict[str, Any]] = []

    # Enrich each account with a small GAQL query for its name + manager flag
    for rn in resource_names:
        customer_id = rn.split("/")[-1]
        try:
            q = (
                "SELECT customer.id, customer.descriptive_name, "
                "customer.currency_code, customer.time_zone, customer.manager FROM customer"
            )
            gaql_url = f"{API_BASE}/{API_VERSION}/customers/{customer_id}/googleAds:search"
            gaql_resp = _rest_post(gaql_url, headers, {"query": q, "pageSize": 1})
            descriptive_name = None
            manager = None
            if gaql_resp.get("results"):
                cust = gaql_resp["results"][0].get("customer", {})
                # handle either snake_case or camelCase that appears in REST mapping
                descriptive_name = cust.get("descriptiveName") or cust.get("descriptive_name")
                manager = cust.get("manager")
            out.append(
                {
                    "customer_id": customer_id,
                    "resource_name": rn,
                    "descriptive_name": descriptive_name,
                    "manager": manager,
                }
            )
        except Exception:
            # If GAQL enrich fails, still return the ID
            out.append({"customer_id": customer_id, "resource_name": rn})

    return out


@mcp.tool()
def run_gaql(
    customer_id: str,
    query: str,
    login_customer_id: Optional[str] = None,
    page_size: int = 1000,
    max_pages: int = 10,
) -> Dict[str, Any]:
    """
    Execute a GAQL query against a given customer account.
    Returns combined results and basic paging metadata.
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

    return {"customer_id": customer_id, "result_count": len(all_results), "results": all_results, "pages": pages}


@mcp.tool()
def run_keyword_planner(
    customer_id: str,
    keywords: List[str],
    language_id: str = "1000",  # English
    geo_target_constants: Optional[List[str]] = None,  # e.g., ["2840"] for US
    page_url: Optional[str] = None,
    login_customer_id: Optional[str] = None,
    include_adult: bool = False,
    keyword_plan_network: str = "GOOGLE_SEARCH_AND_PARTNERS",
) -> Dict[str, Any]:
    """
    Generate keyword ideas via KeywordPlanIdeaService.generateKeywordIdeas (REST).
    """
    if not DEVELOPER_TOKEN:
        raise RuntimeError("GOOGLE_ADS_DEVELOPER_TOKEN is not set")
    if not customer_id or not keywords:
        raise RuntimeError("customer_id and keywords are required")

    access_token = _get_access_token()
    headers = _ads_headers(access_token, login_customer_id)

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
        metrics = item.get("keywordIdeaMetrics", {})
        ideas.append(
            {
                "text": item.get("text"),
                "avgMonthlySearches": metrics.get("avgMonthlySearches"),
                "competition": metrics.get("competition"),
                "lowTopOfPageBidMicros": metrics.get("lowTopOfPageBidMicros"),
                "highTopOfPageBidMicros": metrics.get("highTopOfPageBidMicros"),
            }
        )
    return {"customer_id": customer_id, "count": len(ideas), "ideas": ideas}


# ----------------------------
# ASGI app with /mcp endpoint
# ----------------------------
# The SDK returns an ASGI app that exposes /mcp by default.
# Running this app with uvicorn yields a server where your MCP endpoint is at /mcp.
app = mcp.streamable_http_app()


if __name__ == "__main__":
    # Cloud Run contract: listen on 0.0.0.0:$PORT (default port 8080)
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

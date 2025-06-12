# 🔐 Token Management System

The Google Ads MCP Server now includes a sophisticated token management system that handles OAuth authentication via web endpoints, similar to the `auth-mcp-tools` approach.

## 🎯 Overview

Instead of requiring local OAuth setup, the server now provides token management tools that:
- Handle OAuth flow via web endpoints
- Store tokens locally in the project directory
- Automatically refresh expired tokens
- Provide easy token management commands

## 🛠️ Available Token Tools (5 Tools)

### 1. `check_google_ads_token_status`
Check if access token and refresh token exist in the code directory and their status.

**Purpose:** Only checks token status, does NOT generate or refresh tokens.

```python
# When tokens exist and are valid
{
  "status": "tokens_found",
  "has_access_token": true,
  "has_refresh_token": true,
  "is_expired": false,
  "expires_at": 1703123456,
  "message": "Access token: ✅ Present, Refresh token: ✅ Present, Status: 🟢 Valid",
  "action_needed": "Use refresh_google_ads_token if expired, or generate_google_ads_token if tokens missing"
}

# When no tokens exist
{
  "status": "no_tokens",
  "message": "No access token or refresh token found in code directory",
  "has_access_token": false,
  "has_refresh_token": false,
  "is_expired": null,
  "action_needed": "Use generate_google_ads_token to create new tokens"
}
```

### 2. `generate_google_ads_token`
Generate new access token and refresh token using OAuth flow with /start and /get-token endpoints.

**Purpose:** Creates fresh tokens when none exist or when refresh token is also expired.

```python
# Successful token generation
{
  "status": "success",
  "access_token": "ya29.a0AfH6SMC...",
  "message": "New access token and refresh token generated successfully",
  "action": "oauth_flow_completed"
}

# Failed token generation
{
  "status": "error",
  "message": "Failed to generate new token: OAuth flow timeout",
  "action": "oauth_flow_failed"
}
```

### 3. `refresh_google_ads_token`
Refresh access token using existing refresh token.

**Purpose:** Refresh expired access token. If refresh token is expired/invalid, indicates new token generation is needed.

```python
# Successful refresh
{
  "status": "success",
  "access_token": "ya29.a0AfH6SMC...",
  "message": "Access token refreshed successfully using refresh token",
  "action": "token_refreshed"
}

# Refresh token expired/invalid
{
  "status": "error",
  "message": "Refresh token failed: invalid_grant. The refresh token may be expired or invalid.",
  "action_needed": "Use generate_google_ads_token to create new access token and refresh token",
  "reason": "refresh_token_expired_or_invalid",
  "original_error": "invalid_grant"
}

# No refresh token found
{
  "status": "error",
  "message": "No refresh token found in code directory",
  "action_needed": "Use generate_google_ads_token to create new tokens",
  "reason": "missing_refresh_token"
}
```

### 4. `get_google_ads_token_url`
Get the OAuth URL and endpoint information.

**Purpose:** Returns the base URL and endpoints used for OAuth authentication.

```python
{
  "url": "https://reimagine-dev.gomarble.ai/api/authorise/google",
  "message": "This is the base URL for OAuth authentication. Use generate_google_ads_token to start the OAuth flow.",
  "endpoints": {
    "start": "https://reimagine-dev.gomarble.ai/api/authorise/google/start",
    "get_token": "https://reimagine-dev.gomarble.ai/api/authorise/google/get-token",
    "refresh": "https://reimagine-dev.gomarble.ai/api/authorise/google/refresh-token"
  }
}
```

### 5. `ensure_google_ads_token`
Intelligently ensure a valid access token exists - check, create, or overwrite as needed.

**Purpose:** One-stop solution that handles all token scenarios automatically and always returns a working token.

```python
# When no tokens exist
{
  "status": "no_tokens_found",
  "message": "No tokens found in code directory, creating new tokens...",
  "action": "creating_new_tokens",
  "access_token": "ya29.a0AfH6SMC..."
}

# When tokens exist and are valid
{
  "status": "token_valid",
  "message": "Valid access token found, no action needed",
  "action": "using_existing_token",
  "access_token": "ya29.a0AfH6SMC..."
}

# When token expired but refresh succeeds
{
  "status": "token_refreshed",
  "message": "Access token was expired, successfully refreshed using refresh token",
  "action": "refreshed_token",
  "access_token": "ya29.a0AfH6SMC..."
}

# When refresh fails, creates new tokens
{
  "status": "refresh_failed_creating_new",
  "message": "Refresh failed (invalid_grant), creating new tokens...",
  "action": "refresh_failed_creating_new",
  "refresh_error": "invalid_grant",
  "access_token": "ya29.a0AfH6SMC..."
}

# When error occurs but recovers
{
  "status": "error_recovered",
  "message": "Error occurred (corrupted JSON), but successfully created new tokens",
  "action": "error_recovery_new_tokens",
  "original_error": "corrupted JSON",
  "access_token": "ya29.a0AfH6SMC..."
}
```

## 🚀 Quick Start Workflow

### Option A: Simple One-Step Approach (Recommended)
```bash
# This handles everything automatically - check, create, refresh, or overwrite
ensure_google_ads_token(api_key="your_api_key")
```

**What happens automatically:**
- ✅ Checks if tokens exist in code directory
- ✅ If no tokens: Creates new ones via OAuth flow
- ✅ If tokens exist but expired: Tries refresh first
- ✅ If refresh fails: Creates new tokens automatically
- ✅ If tokens corrupted: Overwrites with new tokens
- ✅ Always returns a working access token

### Option B: Manual Step-by-Step Approach

### Step 1: Check Token Status
```bash
# First, check if tokens exist in code directory
check_google_ads_token_status(api_key="your_api_key")
```

### Step 2: Generate Tokens (if needed)
```bash
# If no tokens exist or refresh token is expired
generate_google_ads_token(api_key="your_api_key")
```

### Step 3: Refresh When Needed
```bash
# When access token expires, refresh it
refresh_google_ads_token(api_key="your_api_key")
```

### Step 4: Use Google Ads Tools
```bash
# Now you can use any Google Ads tool with the token
list_accounts(
    google_access_token="ya29.a0AfH6SMC...",
    api_key="your_api_key"
)
```

## 💡 **Recommendation**
Use `ensure_google_ads_token` for the simplest experience - it handles all scenarios automatically and always gives you a working token!

## 🔄 Automatic Token Management

The system handles token lifecycle automatically:

### Token Storage
- Tokens stored in `google_ads_credentials.json` in project directory
- Includes access token, refresh token, and expiration time
- Secure local storage, not transmitted anywhere

### Auto-Refresh
- Tokens automatically refreshed 5 minutes before expiration
- Uses refresh token to get new access token
- Seamless operation without user intervention

### Error Handling
- If refresh fails, automatically starts new OAuth flow
- Clear error messages for troubleshooting
- Graceful fallback to manual authentication

## 📁 File Structure

After authentication, you'll have:

```
your-project/
├── google_ads_credentials.json  # Local token storage
├── server.py                    # MCP server
└── ...
```

**Example `google_ads_credentials.json`:**
```json
{
  "google_access_token": "ya29.a0AfH6SMC...",
  "google_refresh_token": "1//04...",
  "google_expires_at": 1703123456,
  "google_token_type": "Bearer",
  "google_scope": "https://www.googleapis.com/auth/adwords"
}
```

## 🔧 Advanced Usage

### Force Token Refresh
```bash
# Force refresh even if token is still valid
get_google_ads_token(
    api_key="your_api_key",
    force_refresh=True
)
```

### Check Token Status
```bash
# View all stored credential information
get_stored_google_ads_credentials(api_key="your_api_key")
```

### Reset Authentication
```bash
# Clear all tokens and start fresh
clear_google_ads_credentials(api_key="your_api_key")

# Then get new token
get_google_ads_token(api_key="your_api_key")
```

## 🚨 Troubleshooting

### 🎯 **Quick Fix for Any Token Issue**
```bash
# This handles ALL token problems automatically
ensure_google_ads_token(api_key="your_api_key")
```
**This tool automatically handles:**
- No credentials found
- Token expired
- Refresh token failed
- Corrupted tokens
- Invalid JSON
- Any other token-related issues

### 🔧 **Manual Troubleshooting (if needed)**

### "No credentials found"
```bash
# Option 1: Automatic fix
ensure_google_ads_token(api_key="your_api_key")

# Option 2: Manual steps
check_google_ads_token_status(api_key="your_api_key")
generate_google_ads_token(api_key="your_api_key")
```

### "Token expired" or "Invalid token"
```bash
# Option 1: Automatic fix
ensure_google_ads_token(api_key="your_api_key")

# Option 2: Manual steps
check_google_ads_token_status(api_key="your_api_key")
refresh_google_ads_token(api_key="your_api_key")
# If refresh fails, use generate_google_ads_token
```

### "Refresh token failed" or "Refresh token expired"
```bash
# Option 1: Automatic fix
ensure_google_ads_token(api_key="your_api_key")

# Option 2: Manual step
generate_google_ads_token(api_key="your_api_key")
```

### "Browser doesn't open"
- The OAuth URL will be logged in the console
- Copy and paste it manually into your browser
- Complete the authentication flow there

### "OAuth flow timeout"
```bash
# Try again - ensure_google_ads_token will retry automatically
ensure_google_ads_token(api_key="your_api_key")
```

### "Corrupted tokens" or "Invalid JSON"
```bash
# ensure_google_ads_token automatically detects and fixes corrupted tokens
ensure_google_ads_token(api_key="your_api_key")
```

## 🔒 Security Notes

- **Local Storage**: Tokens stored locally, never transmitted to external servers
- **Automatic Cleanup**: Expired tokens automatically refreshed or cleared
- **Secure Endpoints**: OAuth flow uses HTTPS endpoints
- **No Persistent Storage**: Tokens only stored locally in your project

## 🆚 Comparison with Previous System

| Feature | Old System | New System |
|---------|------------|------------|
| Setup Complexity | Complex OAuth setup | Simple web-based flow |
| Token Storage | Manual file management | Automatic local storage |
| Token Refresh | Manual refresh required | Automatic refresh |
| Browser Integration | Local server required | Web endpoint based |
| Error Recovery | Manual intervention | Automatic fallback |

## 📚 Integration Examples

### Basic Usage
```python
# 1. Get token
token_response = get_google_ads_token(api_key="your_key")
access_token = token_response["access_token"]

# 2. Use with Google Ads tools
accounts = list_accounts(
    google_access_token=access_token,
    api_key="your_key"
)
```

### Error Handling
```python
# Robust token handling
try:
    token_response = get_google_ads_token(api_key="your_key")
    if token_response["status"] == "success":
        access_token = token_response["access_token"]
        # Use token...
    else:
        print(f"Token error: {token_response['message']}")
except Exception as e:
    print(f"Authentication failed: {e}")
```

This new system provides a much smoother authentication experience while maintaining security and reliability! 🎉 
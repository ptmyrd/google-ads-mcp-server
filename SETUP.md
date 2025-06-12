# Google Ads MCP Server Setup Guide

## 🚀 Quick Setup (2 Files + 1 Environment Variable)

### Step 1: Install Dependencies
```bash
pip install fastmcp requests python-dotenv
```

### Step 2: Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your Google Ads Developer Token
# Get it from: https://developers.google.com/google-ads/api/docs/first-call/dev-token
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
```

### Step 3: Web-Based OAuth (No Setup Required!)

**No OAuth setup needed!** The server uses web-based OAuth endpoints that handle all the authentication automatically:

- ✅ **No client_secret.json file needed**
- ✅ **No Google Cloud Console setup required**
- ✅ **Automatic token management**
- ✅ **Browser-based authentication**

### Step 4: Test the Setup
```bash
# Run the test script
python3 test_simple.py

# Start the server
python3 server.py
```

## 📁 Required Files

After setup, your directory should look like:

```
google_ads_with_fastmcp/
├── server.py                   # ✅ Main server (provided)
├── .env                       # ✅ Your developer token
├── credentials.json           # ⏳ Auto-generated after first auth
└── ...other files
```

## 🔐 Authentication Flow

1. **First Time Setup:**
   ```bash
   # Start server and use token management tools
   python3 server.py
   
   # In Claude Desktop, ask:
   # "Generate a Google Ads token"
   ```

2. **What Happens:**
   - Browser opens to Google OAuth consent screen automatically
   - You authorize the application
   - Tokens are automatically retrieved and saved
   - No manual code entry required
   - Tokens are saved to `credentials.json`

3. **Future Use:**
   - Tokens are automatically refreshed
   - No manual intervention needed

## 🛠️ Troubleshooting

### "client_secret.json not found"
- Download OAuth credentials from Google Cloud Console
- Save as `client_secret.json` in project root

### "Redirect URI mismatch"
- Ensure redirect URI is exactly: `https://localhost:3000/api/authorise/google/callback`
- Check both Google Cloud Console and your client_secret.json

### "Developer token invalid"
- Apply for Google Ads Developer Token
- Add it to `.env` file
- Ensure no extra spaces or quotes

## 📋 Available Tools

Once authenticated, you can use these tools in Claude Desktop:

- `check_google_ads_token_status` - Check token status
- `generate_google_ads_token` - Create new tokens
- `refresh_google_ads_token` - Refresh existing tokens
- `get_google_ads_oauth_info` - Get OAuth configuration
- `run_gaql` - Execute GAQL queries
- `list_accounts` - List Google Ads accounts
- `run_keyword_planner` - Generate keyword ideas

## 🎯 Claude Desktop Integration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python3",
      "args": ["/path/to/your/google_ads_with_fastmcp/server.py"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "your_developer_token"
      }
    }
  }
}
```

That's it! 🎉 
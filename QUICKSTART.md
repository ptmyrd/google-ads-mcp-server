# 🚀 Quick Start Guide

Get up and running with Google Ads MCP Server in 3 simple steps!

## Prerequisites

1. **Google Ads Developer Token**: Apply at [Google Ads API](https://developers.google.com/google-ads/api/docs/first-call/dev-token)
2. **Google Cloud Project**: With Google Ads API enabled
3. **OAuth Credentials**: Create OAuth 2.0 Client ID and download `client_secret.json`
   - 📖 **Detailed setup guide**: [OAUTH_SETUP.md](./OAUTH_SETUP.md)
   - ⚠️ **Important**: Must add redirect URI: `http://localhost:3000/`

## 🏃‍♂️ Quick Setup

### 1. Interactive Setup
```bash
# Clone and enter directory
git clone https://github.com/yourusername/google-ads-mcp.git
cd google-ads-mcp

# Run automated setup
python setup.py
```

The setup will ask for:
- **Google Ads Developer Token** 
- **Path to client_secret.json file** (e.g., `~/Downloads/client_secret.json`)
- **Manager Account ID** (optional, only if using a manager account)

### 2. Install and Run
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
fastmcp run server.py
```

### 3. Authenticate
On first run, your browser will open automatically for Google OAuth authentication. Once complete, the server will be ready!

## 🎯 What You Need

| Required | Item | Where to Get |
|----------|------|--------------|
| ✅ | Developer Token | [Google Ads API Console](https://developers.google.com/google-ads/api/docs/first-call/dev-token) |
| ✅ | client_secret.json | [OAuth Setup Guide](./OAUTH_SETUP.md) → **Must add: `http://localhost:3000/`** |

## 📋 After Setup

Your project will have:
- `.env` file with your configuration
- `google_ads_token.json` (auto-generated after OAuth)

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

1. **Create .env file:**
```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CREDENTIALS_PATH=/path/to/your/client_secret.json
```

2. **Download client_secret.json** from Google Cloud Console and update the path in .env

3. **Run the server** - OAuth will trigger automatically

## 📞 Support

- See [README.md](./README.md) for full documentation
- Check [CLAUDE_INTEGRATION.md](./CLAUDE_INTEGRATION.md) for Claude setup
- Run tests: `python test_mcp_connection.py`

---

**That's it!** Your Google Ads MCP Server is ready to use with Claude Desktop. 🎉 
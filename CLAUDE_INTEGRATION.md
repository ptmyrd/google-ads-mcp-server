# 🖥️ Claude Desktop Integration Guide

This guide shows you how to connect your Google Ads MCP Server to Claude Desktop using the [FastMCP framework](https://github.com/jlowin/fastmcp).

## 📋 Prerequisites

- Claude Desktop installed
- Google Ads MCP Server set up (see [QUICKSTART.md](QUICKSTART.md))
- OAuth credentials configured
- Python 3.10+ installed

## 🔌 Connection Methods

### Method 1: STDIO Transport (Recommended)

**Best for:** Local development, personal use, direct Claude Desktop integration

#### Step 1: Locate Claude Config File

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

#### Step 2: Configure Claude Desktop

Create or update your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["/absolute/path/to/your/google-ads-mcp-server/server.py"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "your_developer_token_here",
        "GOOGLE_ADS_CREDENTIALS_PATH": "/absolute/path/to/credentials/client_secret.json",
        "GOOGLE_ADS_AUTH_TYPE": "oauth"
      }
    }
  }
}
```

**⚠️ Important:** Use absolute paths, not relative paths like `./server.py`

#### Step 3: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. OAuth flow will trigger automatically on first connection

### Method 2: HTTP Transport

**Best for:** Remote deployment, multiple clients, web-based access

#### Step 1: Modify Server for HTTP

Update your `server.py` to use HTTP transport:

```python
if __name__ == "__main__":
    # HTTP transport for remote access
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
```

#### Step 2: Start HTTP Server

```bash
python server.py
```

Server will start at: `http://127.0.0.1:8000/mcp`

#### Step 3: Configure Claude Desktop

```json
{
  "mcpServers": {
    "google-ads": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Method 3: SSE Transport (Legacy)

For compatibility with older MCP clients:

```python
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)
```

Claude config:
```json
{
  "mcpServers": {
    "google-ads": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

## 🔐 Authentication Flow

### First-Time Setup

1. **Start Claude Desktop** with the new configuration
2. **OAuth Trigger:** Server automatically initiates OAuth flow
3. **Browser Opens:** Google OAuth consent screen appears
4. **Grant Access:** Click "Allow" to grant Google Ads API permissions
5. **Success:** Credentials saved, connection established

### Subsequent Uses

- Saved credentials are automatically used
- No browser popup required
- Automatic token refresh when needed

## 🛠️ Configuration Examples

### Basic Configuration

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["/Users/yourname/projects/google-ads-mcp-server/server.py"]
    }
  }
}
```

### With Environment Variables

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "your_token",
        "GOOGLE_ADS_CREDENTIALS_PATH": "/path/to/credentials.json",
        "GOOGLE_ADS_AUTH_TYPE": "oauth",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "1234567890"
      }
    }
  }
}
```

### Multiple MCP Servers

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python",
      "args": ["/path/to/google-ads-server/server.py"]
    },
    "another-server": {
      "command": "python", 
      "args": ["/path/to/another-server/server.py"]
    }
  }
}
```

## 📖 Usage in Claude

### Basic Queries

```
"List my Google Ads accounts"

"Show campaign performance for the last 30 days"

"Generate keyword ideas for 'machine learning'"
```

### Advanced GAQL Queries

```
"Run this GAQL query: SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS"

"Get keyword performance data for campaigns with more than 1000 impressions"

"Show me ad group performance sorted by cost"
```

### Account Management

```
"What accounts do I have access to?"

"Show me manager account details"

"List sub-accounts under my manager account"
```

## 🔍 Troubleshooting

### Claude Can't Connect

1. **Check Configuration File:**
   ```bash
   # Verify file exists and is valid JSON
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

2. **Verify Absolute Paths:**
   ```bash
   # Test if server runs independently
   python /absolute/path/to/your/server.py
   ```

3. **Check Permissions:**
   ```bash
   # Ensure files are readable
   ls -la /path/to/your/credentials/
   ```

### OAuth Issues

1. **Browser Doesn't Open:**
   - Check console logs for OAuth URL
   - Copy URL and open manually in browser

2. **"Authentication Failed":**
   - Verify Developer Token is approved
   - Check Client ID and Secret are correct
   - Ensure Google Ads API is enabled

3. **"Token Expired":**
   ```bash
   # Remove old token and re-authenticate
   rm /path/to/credentials/google_ads_token.json
   ```

### Common Errors

1. **"ModuleNotFoundError":**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **"Permission Denied":**
   ```bash
   # Check file permissions
   chmod 600 /path/to/credentials/client_secret.json
   ```

3. **"Invalid JSON Configuration":**
   ```bash
   # Validate JSON syntax
   python -c "import json; json.load(open('claude_desktop_config.json'))"
   ```

## 🔄 Server Management

### Starting the Server

```bash
# STDIO mode (for Claude Desktop)
python server.py

# HTTP mode (for web access)
python server.py --transport http --port 8000

# With debug logging
PYTHONPATH=. python server.py --debug
```

### Monitoring

```bash
# Check if server is running
ps aux | grep server.py

# Monitor logs
tail -f server.log

# Test connection
curl http://localhost:8000/mcp/health
```

### Auto-Start (Optional)

Create a systemd service (Linux) or launchd service (macOS) to auto-start the server:

**systemd example:**
```ini
[Unit]
Description=Google Ads MCP Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/google-ads-mcp-server
Environment=PYTHONPATH=/path/to/google-ads-mcp-server
ExecStart=/usr/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🧪 Testing Connection

### Test Script

```python
#!/usr/bin/env python3
"""Test Claude MCP connection"""

import asyncio
from fastmcp import Client

async def test_connection():
    try:
        async with Client("./server.py") as client:
            # Test basic connection
            tools = await client.list_tools()
            print(f"✅ Connected! Available tools: {[t.name for t in tools]}")
            
            # Test a simple tool
            if any(t.name == "list_accounts" for t in tools):
                result = await client.call_tool("list_accounts", {})
                print(f"✅ Tool test successful: {result.text[:100]}...")
            
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
```

### Run Test

```bash
python test_connection.py
```

## 📚 Additional Resources

- **FastMCP Documentation:** [https://github.com/jlowin/fastmcp](https://github.com/jlowin/fastmcp)
- **MCP Specification:** [Model Context Protocol](https://modelcontextprotocol.io/)
- **Claude Desktop:** [Official Documentation](https://docs.anthropic.com/)
- **Google Ads API:** [Developer Guide](https://developers.google.com/google-ads/api)

## 🆘 Getting Help

1. **Check Logs:** Look at Claude Desktop console and server logs
2. **Test Independently:** Run `python server.py` to test without Claude
3. **Verify Credentials:** Ensure OAuth setup is working
4. **Community:** Ask questions in MCP or FastMCP communities
5. **Issues:** Report bugs in the GitHub repository

---

**Happy MCP integration! 🚀** 
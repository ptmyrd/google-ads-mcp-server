# Google Ads MCP Server 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-v2.8.0-green.svg)](https://github.com/jlowin/fastmcp)

## Easy One-Click Setup

For a simpler setup experience, we offer ready-to-use installers:

👉 **Download installer -** [https://gomarble.ai/mcp](https://gomarble.ai/mcp)

## Join our community for help and updates

👉 **Slack Community -** [AI in Ads](https://join.slack.com/t/ai-in-ads/shared_invite/zt-379x2i0nk-W3VSAh2c6uddFgxxksA2oQ)

**A FastMCP-powered Model Context Protocol server for Google Ads API integration**

Connect Google Ads API directly to Claude Desktop and other MCP clients with OAuth 2.0 authentication, GAQL querying, and keyword research capabilities.

## ✨ Features

- 🔐 **Web-Based OAuth Authentication** - Secure Google Ads API access
- 📊 **GAQL Query Execution** - Run any Google Ads Query Language queries
- 🏢 **Account Management** - List and manage Google Ads accounts
- 🔍 **Keyword Research** - Generate keyword ideas with search volume data
- 🚀 **FastMCP Framework** - Built on the modern MCP standard
- 🖥️ **Claude Desktop Ready** - Direct integration with Claude Desktop
- 🔄 **Auto Token Refresh** - Seamless credential management

## 📋 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `run_gaql` | Execute GAQL queries | `customer_id`, `query` |
| `list_accounts` | List accessible Google Ads accounts | None |
| `run_keyword_planner` | Generate keyword ideas | `customer_id`, `keywords`, `page_url` (optional) |
| `check_google_ads_token_status` | Check token status | None |
| `generate_google_ads_token` | Create new tokens | None |
| `refresh_google_ads_token` | Refresh existing tokens | None |
| `get_google_ads_oauth_info` | Get OAuth configuration | None |
| `ensure_google_ads_token` | Smart token management | None |

## 🚀 Quick Start

### 1. Setup & Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/google-ads-mcp-server.git
cd google-ads-mcp-server

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your Google Ads Developer Token
```

### 2. Web-Based OAuth Authentication

Good news! Our server uses web-based OAuth authentication that handles everything for you:

- ✅ **No Google Cloud Console setup required**
- ✅ **No client_secret.json file needed**
- ✅ **Automatic token management**
- ✅ **Browser-based authentication**

Just add your Google Ads Developer Token to the `.env` file and you're ready!

## 🖥️ Connecting to Claude Desktop

### Method 1: STDIO Transport (Recommended)

Add this configuration to your Claude Desktop settings:

**Location of Claude config:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "python3",
      "args": ["/path/to/your/google-ads-mcp-server/server.py"]
    }
  }
}
```

### Method 2: HTTP Transport (Alternative)

For web deployment or remote access:

1. **Start the HTTP server:**
   ```bash
   # Modify server.py to use HTTP transport
   mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
   ```

2. **Claude Desktop config:**
   ```json
   {
     "mcpServers": {
       "google-ads": {
         "url": "http://127.0.0.1:8000/mcp"
       }
     }
   }
   ```

### 3. First Run Authentication

1. **Start Claude Desktop** with the new configuration
2. **Use Token Tools:** Ask Claude to generate a Google Ads token
3. **OAuth Flow:** Browser will automatically open for Google authentication
4. **Grant Permissions:** Allow access to Google Ads API
5. **Authentication Complete:** Tokens are automatically retrieved and saved to `credentials.json`

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Google Ads API Configuration
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
```

That's it! Tokens are automatically stored in `credentials.json` in your project directory.

### Transport Options

The server supports multiple transport protocols:

```python
# STDIO (Default - for Claude Desktop)
mcp.run()

# HTTP (for web deployment)
mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")

# SSE (for legacy clients)
mcp.run(transport="sse", host="127.0.0.1", port=8000)
```

## 📖 Usage Examples

### In Claude Desktop

Once connected, you can ask Claude to:

```
"List all my Google Ads accounts"

"Show me campaign performance for account 1234567890 in the last 30 days"

"Generate keyword ideas for 'digital marketing' and 'SEO services'"

"Run a GAQL query to get ad group performance data"
```

### Example GAQL Queries

```sql
-- Campaign Performance
SELECT 
  campaign.id,
  campaign.name, 
  metrics.clicks, 
  metrics.impressions,
  metrics.cost_micros
FROM campaign 
WHERE segments.date DURING LAST_30_DAYS

-- Keyword Performance  
SELECT 
  campaign.id,
  ad_group_criterion.keyword.text, 
  ad_group_criterion.keyword.match_type,
  metrics.ctr,
  metrics.average_cpc
FROM keyword_view 
WHERE segments.date DURING LAST_7_DAYS
ORDER BY metrics.impressions DESC
```

## 🏗️ Project Structure

```
.
├── constant/                    # Configuration constants
│   ├── __init__.py             # Constants exports  
│   └── constant.py             # API constants
├── server.py                   # Main FastMCP server with token management
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables (your developer token)
├── credentials.json           # Auto-generated OAuth tokens (access/refresh)
└── README.md                  # This file
```

## 🔒 Security & Production

### Best Practices

1. **Secure Credential Storage:**
   ```bash
   # Set proper file permissions
   chmod 600 .env
   chmod 600 credentials.json
   ```

2. **Environment Variables:**
   - Never commit `.env` or credential files to git
   - Use environment variables in production
   - Add credential files to .gitignore

3. **Network Security:**
   - Use HTTPS in production
   - Implement rate limiting
   - Monitor API usage

## 🛠️ Troubleshooting

### Common Issues

1. **"Token generation failed"**
   - Check your developer token in `.env`
   - Ensure you have internet access
   - Try running `check_google_ads_token_status` tool

2. **"Module not found"**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Check Python path
   python3 -c "import fastmcp; print('FastMCP installed')"
   ```

3. **"OAuth browser doesn't open"**
   - Check if running in headless environment
   - Copy OAuth URL from console logs manually

4. **"Claude can't connect"**
   - Verify `claude_desktop_config.json` path
   - Check absolute paths in configuration
   - Restart Claude Desktop after config changes

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests
4. **Commit changes:** `git commit -m 'Add amazing feature'`
5. **Push to branch:** `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/google-ads-mcp-server.git
cd google-ads-mcp-server

# Install development dependencies
pip install -r requirements.txt
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### MIT License

Copyright (c) 2025 Google Ads MCP Server Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) - The fast, Pythonic way to build MCP servers
- Google Ads API for providing comprehensive advertising data access
- Model Context Protocol for enabling seamless AI integration

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/google-ads-mcp-server/issues)
- **Google Ads API:** [Official Documentation](https://developers.google.com/google-ads/api)
- **Join our Slack:** [AI in Ads](https://join.slack.com/t/ai-in-ads/shared_invite/zt-379x2i0nk-W3VSAh2c6uddFgxxksA2oQ)

---

**Made with ❤️ for the MCP community** 
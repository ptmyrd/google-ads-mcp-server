# Google Ads OAuth Setup Guide

This document explains how to set up and use OAuth 2.0 authentication with the Google Ads FastMCP server.

## Project Structure

```
.
├── auth/                    # Authentication module
│   ├── __init__.py         # Auth module exports
│   └── oauth.py            # OAuth implementation
├── constant/               # Constants module
│   ├── __init__.py         # Constants module exports
│   └── constant.py         # All constants and configuration
├── server.py               # Main FastMCP server
├── requirements.txt        # Python dependencies
└── env.example            # Environment variables example
```

## Prerequisites

1. **Google Cloud Console Setup**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Ads API
   - Create OAuth 2.0 credentials (Desktop Application)
   - Get your Developer Token from Google Ads

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## OAuth Configuration

### Environment Variables

Copy `env.example` to `.env` and fill in your credentials:

```bash
# Google Ads API Configuration
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CREDENTIALS_PATH=./credentials/google_ads_token.json

# OAuth 2.0 Configuration
GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your_client_secret

# Authentication Type
GOOGLE_ADS_AUTH_TYPE=oauth

# Optional: Manager Account Configuration
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_manager_account_id
```

### OAuth Flow

The OAuth implementation supports two authentication methods:

#### 1. OAuth 2.0 (Default - Recommended for development)
- **Use case**: Individual users, development, testing
- **Setup**: Requires `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET`
- **Flow**: Opens browser for user consent, saves refresh token

#### 2. Service Account (Production)
- **Use case**: Server-to-server authentication, production
- **Setup**: Requires service account JSON file
- **Flow**: Uses service account credentials directly

## Getting Started

### Quick Setup (Recommended)

For the fastest setup, use the automated setup script:

```bash
# Run the interactive setup
python setup.py

# Install dependencies
pip install -r requirements.txt

# Start the server (OAuth will trigger automatically)
fastmcp run server.py
```

### Manual Setup

#### Step 1: Set Up OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client IDs"
5. Choose "Desktop application"
6. Download the client configuration JSON file

#### Step 2: Get Developer Token

1. Go to [Google Ads Console](https://ads.google.com/)
2. Navigate to "Tools & Settings" > "Setup" > "API Center"
3. Apply for a Developer Token
4. Wait for approval (can take a few days)

#### Step 3: Configure Environment

```bash
# Create credentials directory
mkdir credentials

# Create .env file
cp env.example .env

# Place your downloaded OAuth JSON file
mv downloaded-client-secrets.json ./credentials/client_secret.json

# Edit .env with your credentials
nano .env
```

#### Step 4: First Run

```bash
fastmcp run server.py
```

On first run:
1. **🔐 OAuth Flow Initiated**: Browser opens automatically
2. **✅ Grant Permissions**: Allow access to Google Ads
3. **💾 Token Saved**: Credentials saved for future use
4. **🚀 Server Ready**: MCP server starts and stays running

## Authentication Module Usage

### Basic Usage

```python
from auth import get_credentials, get_headers

# Get authenticated credentials
creds = get_credentials()

# Get headers for API requests
headers = get_headers(creds)

# Use headers in your requests
response = requests.get(url, headers=headers)
```

### Available Functions

```python
from auth import (
    get_credentials,              # Main function to get credentials
    get_oauth_credentials,        # Get OAuth credentials specifically
    get_service_account_credentials,  # Get service account credentials
    get_headers,                  # Get API request headers
    format_customer_id,           # Format customer ID
    refresh_credentials_if_needed,  # Refresh expired credentials
    validate_credentials,         # Validate credentials
    save_credentials             # Save credentials to file
)
```

## Constants Module Usage

```python
from constant import (
    GOOGLE_ADS_DEVELOPER_TOKEN,
    API_VERSION,
    ENDPOINTS,
    SCOPES
)

# Use in your API calls
url = ENDPOINTS['LIST_CUSTOMERS']
```

## Troubleshooting

### Common Issues

1. **"Invalid credentials"**
   - Check that your Client ID and Secret are correct
   - Ensure the OAuth consent screen is configured
   - Verify that the Google Ads API is enabled

2. **"Developer token not approved"**
   - Apply for developer token approval in Google Ads console
   - Use a test account while waiting for approval

3. **"Token expired"**
   - Delete the saved token file and re-authenticate
   - The system should automatically refresh tokens

4. **"Import errors"**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that the folder structure is correct

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Secure token storage**
   - Store tokens in secure location
   - Set appropriate file permissions (600)

3. **Regular token rotation**
   - Monitor token expiration
   - Implement automatic refresh

4. **Use Service Accounts in Production**
   - More secure for server-to-server authentication
   - Better for automated systems

## Production Deployment

For production environments:

1. Use Service Account authentication
2. Store credentials in secure credential management system
3. Use environment variables for configuration
4. Implement proper error handling and logging
5. Set up monitoring for authentication failures

## Testing

Test your OAuth setup:

```bash
# Run a simple test
python -c "from auth import get_credentials; print('OAuth setup successful!' if get_credentials() else 'Setup failed')"
```

## Support

For issues with:
- **Google Ads API**: [Google Ads API Documentation](https://developers.google.com/google-ads/api)
- **OAuth Setup**: [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- **This Implementation**: Check the code comments and error messages 
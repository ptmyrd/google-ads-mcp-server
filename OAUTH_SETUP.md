# 🔐 OAuth Client Setup Guide

This guide walks you through creating OAuth 2.0 credentials in Google Cloud Console for the Google Ads MCP Server.

## 📋 Prerequisites

- Google Cloud Project with Google Ads API enabled
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## 🚀 Step-by-Step Setup

### 1. Navigate to Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** → **Credentials**

### 2. Create OAuth 2.0 Client ID

1. Click **+ CREATE CREDENTIALS**
2. Select **OAuth 2.0 Client ID**
3. If prompted, configure the OAuth consent screen first

### 3. Configure OAuth Consent Screen (if needed)

1. Choose **External** user type (unless you're in a Google Workspace organization)
2. Fill in required fields:
   - **App name**: "Google Ads MCP Server" (or your preferred name)
   - **User support email**: Your email
   - **Developer contact information**: Your email
3. Add scopes: **Google Ads API** (`https://www.googleapis.com/auth/adwords`)
4. Add test users (your email address)

### 4. Configure OAuth Client

1. **Application type**: Select **Desktop application**
2. **Name**: "Google Ads MCP Client" (or your preferred name)

### 5. ⚠️ **IMPORTANT: Add Redirect URIs**

In the **Authorized redirect URIs** section, add this URI:

```
http://localhost:3000/
```

**Why this URI?**
- The OAuth flow uses port 3000 consistently
- This is the standard callback URL for the Google Ads MCP Server
- Using a fixed port makes the setup more predictable and reliable
- The Google OAuth library handles the callback automatically at the root path

### 6. Download Credentials

1. Click **CREATE**
2. In the popup, click **DOWNLOAD JSON**
3. Save the file as `client_secret.json`
4. Note the download location (e.g., `~/Downloads/client_secret.json`)

## 📁 File Structure

Your downloaded `client_secret.json` should look like this:

```json
{
  "installed": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": [
      "http://localhost:3000/"
    ]
  }
}
```

## 🔧 Next Steps

1. **Update your .env file** with the path to your `client_secret.json`:
   ```bash
   GOOGLE_ADS_CREDENTIALS_PATH=/path/to/your/client_secret.json
   ```

2. **Run the server**:
   ```bash
   fastmcp run server.py
   ```

3. **Complete OAuth flow**: Your browser will open automatically for authentication

## 🚨 Troubleshooting

### "redirect_uri_mismatch" Error

If you get this error, it means the redirect URI isn't configured correctly:

1. Go back to Google Cloud Console → Credentials
2. Edit your OAuth 2.0 Client ID
3. Ensure you have added: `http://localhost:3000/`
4. The redirect URI must match exactly (including the trailing slash)

### "invalid_client" Error

- Double-check your `client_secret.json` file is valid JSON
- Ensure you downloaded the correct file type (OAuth 2.0 Client ID, not Service Account)

### Browser Doesn't Open

- The OAuth URL will be printed in the console
- Copy and paste it manually into your browser
- Complete the authentication flow there

## 🔒 Security Notes

- Keep your `client_secret.json` file secure
- Don't commit it to version control
- The client secret is not as sensitive as service account keys, but should still be protected
- Redirect URIs to localhost are safe for desktop applications

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Ads API Authentication](https://developers.google.com/google-ads/api/docs/oauth/overview)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app) 
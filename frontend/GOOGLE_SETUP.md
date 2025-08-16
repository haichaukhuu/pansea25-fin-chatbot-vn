# Google Sign-in Setup Guide

## Prerequisites

1. A Google Cloud Platform account
2. A Google Cloud project

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API

### 2. Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "PanSea Financial Chatbot"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users (your email addresses)

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized JavaScript origins:
   - `http://localhost:5173` (for development)
   - `http://localhost:3000` (alternative dev port)
   - Your production domain (when deployed)
5. Add authorized redirect URIs:
   - `http://localhost:5173` (for development)
   - Your production domain (when deployed)
6. Copy the Client ID

### 4. Environment Configuration

Create a `.env` file in the frontend directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000

# Google OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
```

Replace `your_google_client_id_here` with the Client ID from step 3.

### 5. Backend Configuration

Make sure your backend supports Google OAuth authentication. The frontend will send the Google ID token to the `/api/auth/google` endpoint.

## Testing

1. Start the development server: `npm run dev`
2. Go to the login page
3. Click the "Sign in with Google" button
4. Complete the Google OAuth flow
5. You should be redirected to the chat interface with your Google profile information

## Troubleshooting

- **"Invalid Client ID"**: Make sure the Client ID in your `.env` file matches the one from Google Cloud Console
- **"Unauthorized JavaScript origin"**: Add your development URL to the authorized JavaScript origins in Google Cloud Console
- **"Redirect URI mismatch"**: Add your development URL to the authorized redirect URIs in Google Cloud Console

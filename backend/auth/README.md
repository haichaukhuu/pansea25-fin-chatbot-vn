# Firebase Authentication Setup Guide

This guide will walk you through setting up Firebase authentication for the PANSEA25 Financial Chatbot backend.

## Prerequisites

- Firebase project (create one at [Firebase Console](https://console.firebase.google.com))
- Python 3.9 or higher
- Node.js and npm (for frontend)

## 📋 Step-by-Step Setup

### 1. 🔥 Firebase Console Configuration

1. **Navigate to Firebase Console**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Select your project or create a new one

2. **Enable Authentication**
   - In the left sidebar, click on **Authentication**
   - Go to the **Sign-in method** tab
   - Enable your desired authentication methods (Email/Password, Google, etc.)

3. **Get Web API Key**
   - Go to **Project Settings** (gear icon) → **General** tab
   - Scroll down to **Your apps** section
   - If no web app exists, click **Add app** → **Web**
   - Copy the **Web API Key** from the Firebase config object

4. **Generate Service Account Key**
   - Go to **Project Settings** → **Service accounts** tab
   - Click **Generate new private key**
   - Download the JSON file (this will be your `service-account-key.json`)

### 2. 📁 Configure Credentials

1. **Service Account Key**
   - Save the downloaded JSON file as `service-account-key.json`
   - Place it in: `backend/auth/firebase_credentials/`

2. **Environment Variables**
   - Update the `.env` file in `backend/auth/firebase_credentials/`
   - Required variables:
   ```env
   FIREBASE_API_KEY=your_web_api_key_here
   FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_STORAGE_BUCKET=your_project_id.firebasestorage.app
   FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   FIREBASE_APP_ID=your_app_id
   ```

### 3. 🐍 Backend Setup

1. **Navigate to Backend Directory**
   ```cmd
   cd backend
   ```

2. **Create and Activate Virtual Environment**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Start the Backend Server**
   ```cmd
   python run.py
   ```
   or
   ```cmd
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 4. 🖥️ Frontend Setup

1. **Open New Terminal and Navigate to Frontend**
   ```cmd
   cd frontend
   ```

2. **Install Dependencies**
   ```cmd
   npm install
   ```

3. **Start Development Server**
   ```cmd
   npm run dev
   ```

## 🔍 Verification

- **Backend**: Should be running on `http://localhost:8000`
- **Frontend**: Should be running on `http://localhost:5173`
- **API Docs**: Available at `http://localhost:8000/docs`

## 🛠️ Troubleshooting

### Common Issues:

1. **"Firebase Admin SDK initialization failed"**
   - Verify `service-account-key.json` is in the correct location
   - Check that the file has valid JSON syntax

2. **"Firebase Client SDK initialization failed"**
   - Verify all environment variables in `.env` are correctly set
   - Ensure there are no extra spaces or quotes around values

3. **"Module not found" errors**
   - Make sure virtual environment is activated
   - Run `pip install -r requirements.txt` again

4. **CORS errors in frontend**
   - Ensure backend is running on port 8000
   - Check that frontend URL is in the CORS origins list

## 📂 File Structure
```
backend/auth/
├── firebase_credentials/
│   ├── .env                    # Environment variables
│   └── service-account-key.json  # Firebase service account key
├── firebase_config.py          # Firebase configuration
├── firebase_auth_service.py    # Authentication service
└── README.md                   # This file
```

## 🔐 Security Notes

- Never commit `service-account-key.json` or `.env` files to version control
- Keep your Firebase API keys secure
- Regularly rotate your service account keys in production

## 📞 Support

If you encounter issues not covered in this guide, please check:
- [Firebase Documentation](https://firebase.google.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- Project issues on GitHub
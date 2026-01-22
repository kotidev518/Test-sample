# 🎓 AI-Powered Personalized E-Learning Platform

An intelligent e-learning platform that provides personalized learning experiences using AI-driven recommendations, mastery-based progression, and automated quiz generation.

## ✨ Features

- **📺 YouTube Playlist Integration**: Import courses directly from YouTube playlists via the Admin Dashboard
- **🔐 Firebase Authentication**: Secure user registration and login
- **🤖 AI-Powered Quizzes**: Automatically generated quizzes for each video using Google Gemini AI
- **📊 Mastery-Based Learning**: Track progress and unlock content based on quiz performance
- **🎯 Personalized Recommendations**: AI-driven video recommendations based on learning patterns
- **📈 Analytics Dashboard**: Visualize learning progress and performance metrics
- **🎨 Modern UI**: Beautiful, responsive design with dark theme

## 🛠 Tech Stack

### Backend
- **FastAPI** - Python web framework
- **MongoDB Atlas** - Cloud database
- **Firebase Admin SDK** - Authentication verification
- **Google Gemini AI** - Quiz generation and content analysis
- **YouTube Data API** - Playlist and video metadata fetching
- **Sentence Transformers** - Semantic similarity for recommendations

### Frontend
- **React** - UI framework
- **Firebase SDK** - Authentication
- **React YouTube** - Video player integration
- **Chart.js** - Analytics visualizations
- **CSS3** - Custom styling with modern aesthetics

## 📋 Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 16+](https://nodejs.org/)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas) (or local MongoDB)
- [Firebase Project](https://console.firebase.google.com/) with Authentication enabled
- [Google Cloud Console](https://console.cloud.google.com/) for YouTube API and Gemini API keys

## 🔑 Environment Setup

This project requires environment variables and Firebase credentials that are **not** stored in Git.

### 1. Backend Configuration (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` and configure:

```env
# MongoDB Atlas Connection String
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?appName=YourApp

# Database Name
DB_NAME=learning_platform

# JWT Secret (for token signing)
JWT_SECRET=your-secure-secret-key

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Firebase Storage Bucket
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app

# YouTube Data API Key
YOUTUBE_API_KEY=your-youtube-api-key

# Google Gemini API Key
GEMINI_API_KEY=your-gemini-api-key
```

### 2. Firebase Service Account

1. Go to [Firebase Console](https://console.firebase.google.com/) → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save the file as `serviceAccountKey.json` in the `backend/` folder

### 3. Frontend Configuration (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env` and configure:

```env
REACT_APP_BACKEND_URL=http://localhost:8000

# Firebase Configuration (from Firebase Console → Project Settings → General)
REACT_APP_FIREBASE_API_KEY=your-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
REACT_APP_FIREBASE_APP_ID=your-app-id
```

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Final-project.git
cd Final-project
```

### 2. Backend Setup (FastAPI)

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment (Recommended):
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Ensure your `.env` file is configured (see Environment Setup above)

5. Run the Backend Server:
   ```bash
   python server.py
   ```
   - Server running at: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

### 3. Frontend Setup (React)

1. Open a **new** terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # If you encounter peer dependency issues:
   npm install --legacy-peer-deps
   ```

3. Start the Development Server:
   ```bash
   npm start
   ```
   - App running at: `http://localhost:3000`

## 👨‍💼 Admin Features

### Importing Courses from YouTube

1. Sign in with an admin account
2. Navigate to the Admin Dashboard
3. Paste a YouTube playlist URL
4. Click "Import Playlist"
5. The system will automatically:
   - Fetch playlist metadata (title, description, thumbnail)
   - Import all videos from the playlist
   - Generate AI-powered quizzes for each video

## 📚 Project Structure

```
Final-project/
├── backend/
│   ├── app/
│   │   ├── routers/          # API route handlers
│   │   ├── models/           # Data models
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app entry
│   ├── server.py             # Server startup
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── context/          # React context providers
│   │   └── index.js          # React entry point
│   ├── public/               # Static assets
│   └── .env.example          # Environment template
└── README.md
```

## 🔄 Updating the Project

To get the latest changes from the repository:

```bash
git pull origin main
```

After pulling updates:
1. Check for new environment variables in `.env.example` files
2. Run `pip install -r requirements.txt` in the backend
3. Run `npm install` in the frontend

## 🛠 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port Conflicts** | Ensure ports 8000 (backend) and 3000 (frontend) are free |
| **Dependency Conflicts** | Use `npm install --legacy-peer-deps` |
| **Firebase Auth Errors** | Verify your Firebase configuration in `.env` files |
| **MongoDB Connection Failed** | Check your `MONGO_URL` and network access settings |
| **Videos Not Loading** | Ensure YouTube API key is valid and has quota |
| **Quiz Generation Failed** | Verify Gemini API key is configured correctly |

## 📄 License

This project is for educational purposes.

## 👥 Contributors

- Team members of the AI E-Learning Platform project

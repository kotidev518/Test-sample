# 🚀 Installation and Running Guide

This guide provides everything you need to set up, install, and run the AI-Powered E-Learning Platform locally.

## 1. Prerequisites
Ensure you have the following installed:
- **Python 3.8+**
- **Node.js 16+**
- **MongoDB** (Cloud or Local)
- **Redis** (Required for background tasks)
- **Git**

## 2. Setup & Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/kotidev518/Test-sample.git
cd Test-sample
```

### Step 2: Backend Setup
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
pip install arq redis
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
```

## 3. Configuration (Environment Variables)

Create `.env` files in both `backend/` and `frontend/` folders using their `.env.example` templates.

### Key Backend Variables (`backend/.env`):
- `MONGO_URL`: Your MongoDB connection string.
- `FIREBASE_STORAGE_BUCKET`: Your Firebase bucket URL.
- `YOUTUBE_API_KEY`: Google Cloud YouTube API Key.
- `GEMINI_API_KEY`: Google AI Studio API Key.
- `REDIS_URL`: `redis://localhost:6379`

### Firebase Credentials:
Download your `serviceAccountKey.json` from the Firebase Console and place it in the `backend/` directory.

## 4. Running the Application

To run the full system, you need **three** separate terminals.

### Terminal 1: Backend Server
```bash
cd backend
python server.py
```
- API Docs: `http://localhost:8000/docs`

### Terminal 2: Background Worker (ARQ)
```bash
cd backend
python -m arq app.worker.WorkerSettings
```

### Terminal 3: Frontend Client
```bash
cd frontend
npm start
```
- App URL: `http://localhost:3000`

## 🛠 Troubleshooting
- **Redis Connection**: Ensure Redis is running on port 6379.
- **Videos Not Playing**: Check `serviceAccountKey.json` and CORS settings in Firebase.
- **DB Init**: Run `curl -X POST "http://localhost:8000/api/init-data?force=true"` to initialize sample data.

This project consists of a FastAPI backend and a React (Create React App with Craco) frontend.
## Prerequisites
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 16+](https://nodejs.org/)
- [MongoDB](https://www.mongodb.com/try/download/community) (Service must be running locally on port 27017)

## 🔑 Environment Setup
This project requires environment variables and Firebase credentials that are **not** stored in Git.

1. **Backend Configuration**:
   - Copy `backend/.env.example` to `backend/.env` and update values.
   - Obtain the `serviceAccountKey.json` from the team leads and place it in the `backend/` folder.
2. **Frontend Configuration**:
   - Copy `frontend/.env.example` to `frontend/.env` and update values.
## 🚀 Quick Start Guide
### 1. Backend Setup (FastAPI)
1.  Open a terminal and navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create/Activate a virtual environment (Recommended):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate  # Mac/Linux
    ```
3.  Install dependencies:
    ```bash
    
    ```
4.  Configure Environment Variables:
    - Ensure `.env` exists in the `backend` folder with the following:
      ```env
      MONGO_URL=mongodb://localhost:27017
      DB_NAME=learning_platform
      JWT_SECRET=development_secret_key
      CORS_ORIGINS=http://localhost:3000
      ```
5.  Run the Backend Server:
    ```bash
    uvicorn server:app --reload
    ```
    - Server running at: `http://localhost:8000`
    - API Docs: `http://localhost:8000/docs`
### 2. Frontend Setup (React)
1.  Open a **new** terminal and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    # or if you face peer dependency issues (common in this project):
    npm install --legacy-peer-deps
    ```
3.  Start the Development Server:
    ```bash
    npm run dev
    # or
    npm start
    ```
    - App running at: `http://localhost:3000`
## � Updating the Project
To get the latest changes from the repository:
```bash
git pull origin main
```

## �🛠 Troubleshooting
- **Git Issues**: If you see "remote origin already exists", run `git remote remove origin` before adding a new one.
- **Port Conflicts**: Ensure ports 8000 (backend) and 3000 (frontend) are free.
- **Dependency Conflicts**: Use `npm install --legacy-peer-deps` if `npm install` fails
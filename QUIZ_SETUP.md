# 🤖 AI Quiz System Setup

This document focuses on configuring the automated quiz generation system powered by Google Gemini AI and the ARQ background worker.

## 1. Prerequisites
- **Google AI Studio API Key**: Get it from [aistudio.google.com](https://aistudio.google.com/).
- **Redis Server**: Must be running as the message broker for background jobs.

## 2. Configuration
Add these to your `backend/.env`:
```env
# Gemini API Key for Quiz Generation
GEMINI_API_KEY=your-gemini-key

# Redis Connection for Background Tasks
REDIS_URL=redis://127.0.0.1:6379
```

## 3. How it Works
1. **Admin Import**: When an admin imports a YouTube playlist, the metadata is saved immediately.
2. **Background Job**: The system enqueues a background job to fetch transcripts and generate quizzes.
3. **ARQ Worker**: The worker (`WorkerSettings`) processes the queue, calls Gemini AI, and stores the generated MCQs in MongoDB.

## 4. Starting the System
To enable quiz generation, you **must** run the ARQ worker in your backend environment:
```bash
cd backend
python -m arq app.worker.WorkerSettings
```

## 🛠 Troubleshooting
- **No Quizzes Generated**: Check if the ARQ worker terminal shows any errors.
- **Gemini API Limits**: If you are on the free tier, the worker uses exponential backoff to retry if rate-limited.
- **Redis Down**: The worker will fail to start if it cannot connect to the `REDIS_URL`.

# 🧪 Testing Guide

This guide explains how to run the automated test suites for both the backend and frontend.

## 1. Backend Testing (Pytest)
The backend uses `pytest` for unit and integration testing.

### Run all tests:
```bash
cd backend
pytest
```

### Run specific categories:
```bash
# Unit Tests
pytest tests/unit

# Integration Tests
pytest tests/integration
```

### Coverage Report:
```bash
pytest --cov=app tests/
```

## 2. Frontend Testing (Jest)
The frontend uses Jest and React Testing Library.

### Run tests:
```bash
cd frontend
npm test
```

### CI/CD Tip:
Always run these tests before pushing code to the repository to ensure no regressions are introduced.

## 3. Manual Verification Checklist
Before a final push:
- [ ] User Login/Registration works.
- [ ] Admin Dashboard: Playlist import works.
- [ ] Course Page: Videos play and quizzes load.
- [ ] Analytics: Student progress updates correctly.

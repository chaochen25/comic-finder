# Marvel Comic Release Tracker (MVP)

Browse Marvel releases by week (Wed→Tue), search titles, and view details with cover art.

## Features
- Pick a **Wednesday** to see that week’s releases
- **Search** by title
- Toggle **Single issues only** (hide collections)
- **Details modal** with description, on-sale date, issue number, and thumbnail
- (Dev) **Sync current month** from backend

## Tech Stack
- **Frontend**: React (Vite)
- **Backend**: FastAPI (Python), SQLModel, SQLite
- **API**: Marvel (server-side; keys never exposed to browser)

## Local Setup (this project was done on mac)
```bash
# Backend
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install fastapi "uvicorn[standard]" sqlmodel pydantic python-dotenv requests
uvicorn app.main:app --reload --port 8000  # http://127.0.0.1:8000/docs

# Frontend
cd ../frontend
# (optional) nvm use will read .nvmrc
nvm use 22
npm install
npm run dev  # http://localhost:5173

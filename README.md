# Marvel Comic Release Tracker 

A full-stack web application to browse and search upcoming and recent Marvel comic book releases, displayed in a weekly grid format.  
Data is fetched from the ComicVine API and stored locally for fast browsing. The project was supposed to use Marvel's API, but currently it is down. 

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

## Demo Video
[Download Demo Video](assets/demo.mov)


## Local Setup (this project was done on mac)

# Clone Repo
git clone https://github.com/YOUR-USERNAME/comic-finder.git
cd comic-finder

# Backend (Terminal A)
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install fastapi "uvicorn[standard]" sqlmodel pydantic python-dotenv requests
uvicorn app.main:app --reload --port 8000  # http://127.0.0.1:8000/docs

# Frontend (Terminal B)
cd ../frontend
# (optional) nvm use will read .nvmrc
nvm use 22
npm install
npm run dev  # http://localhost:5173

# Backend (Terminal C)
curl -X POST "http://127.0.0.1:8000/api/cv/sync?start=2025-06-01&end=2025-12-31"
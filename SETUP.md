# ClauseWise — Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 18+ | Frontend runtime |
| **npm** | 9+ | Package management |
| **Git** | any | Version control |

## 1. Clone & Navigate

```bash
git clone <repo-url>
cd Virtualprompt
```

## 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set your Gemini API key:

```env
GEMINI_API_KEY=your-actual-gemini-api-key
```

> **Note:** The app works without a Gemini API key using built-in mock responses for development and testing. Set the key only when you want live AI analysis.

### Start the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

Verify:
- **API Base:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health → `{"status": "ok"}`

## 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend will be live at **http://localhost:5173**.

## 4. Run Tests

From the project root:

```bash
python -m pytest backend/tests/ -v -o asyncio_mode=auto
```

Expected: **26 tests pass** (Phases 1–8).

## 5. Docker Compose (Optional)

To run all services together:

```bash
docker-compose up --build
```

Services:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **ChromaDB:** http://localhost:8001

## Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Run from `backend/` directory or ensure `backend` is in your `PYTHONPATH` |
| CORS errors in browser | Ensure backend is running on port 8000 and frontend on port 5173 |
| `GEMINI_API_KEY` not working | The key should be a valid Google AI Studio API key. The app falls back to mock mode if invalid |
| Tests fail with import errors | Ensure virtual environment is activated: `.venv\Scripts\activate` |

"""
ClauseWise – FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ingest, clauses, compare, ask, nextsteps

app = FastAPI(
    title="ClauseWise API",
    description="AI-powered legal document analysis assistant",
    version="0.1.0",
)

# CORS – allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(ingest.router, prefix="/api")
app.include_router(clauses.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(ask.router, prefix="/api")
app.include_router(nextsteps.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "clausewise-api"}

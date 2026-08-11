"""
FRAGMENT Backend — Vercel Serverless Entry Point
Wraps FastAPI with Mangum so Vercel can invoke it as a serverless function.
"""
import sys
import os
import asyncio

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from mangum import Mangum
from app.main import app

# ── Lazy DB Initialization ────────────────────────────────────────────────────
# On Vercel, lifespan events don't fire. We patch a startup event directly
# onto the app so tables are created before the first real request.
_db_initialized = False

@app.on_event("startup")
async def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        try:
            from app.db.session import init_db
            await init_db()
            _db_initialized = True
        except Exception as e:
            print(f"[FRAGMENT] DB init warning: {e}")

# Wrap FastAPI with Mangum — lifespan="auto" so startup event above fires
handler = Mangum(app, lifespan="auto")

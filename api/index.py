"""
FRAGMENT Backend — Vercel Serverless Entry Point
Wraps FastAPI with Mangum for Vercel serverless function invocation.
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from mangum import Mangum
from app.main import app

# ── Lazy DB Initialization ────────────────────────────────────────────────────
# On Vercel, lifespan events may not fire consistently. We patch startup directly.
_db_initialized = False

async def _ensure_db_init():
    global _db_initialized
    if not _db_initialized:
        try:
            from app.db.session import init_db
            await init_db()
            _db_initialized = True
        except Exception as e:
            print(f"[FRAGMENT] DB init: {e}")

@app.on_event("startup")
async def _startup():
    await _ensure_db_init()

# Mangum wraps FastAPI for AWS Lambda / Vercel serverless
# lifespan="off" prevents startup event double-fire issues on Vercel
handler = Mangum(app, lifespan="auto")

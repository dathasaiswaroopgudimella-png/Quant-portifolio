"""
FRAGMENT Backend — Vercel Serverless Entry Point
Wraps FastAPI with Mangum so Vercel can invoke it as a serverless function.
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from mangum import Mangum
from app.main import app

# Wrap FastAPI with Mangum (lifespan="off" prevents serverless startup hanging)
handler = Mangum(app, lifespan="off")

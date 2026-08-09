"""
FRAGMENT Backend — Vercel Serverless Entry Point
Wraps FastAPI with Mangum so Vercel can invoke it as a serverless function.
All routes under /api/* are handled here.
"""
import sys
import os

# Make the backend app importable from this wrapper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from mangum import Mangum
from app.main import app

# Update CORS to allow the Vercel deployment domain
from fastapi.middleware.cors import CORSMiddleware

# Mangum wraps the ASGI app for AWS Lambda / Vercel serverless
handler = Mangum(app, lifespan="auto")

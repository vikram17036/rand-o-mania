from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import api
from app.logger import setup_logging

# Initialize logging
setup_logging()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(title="Rand-o-mania API")
    
    # Add CORS middleware to allow access from anywhere
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    
    # Register routes
    app.include_router(api.router)
    
    return app


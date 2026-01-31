"""
FastAPI server for Obelisk Core
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import importlib.util

# Import config from root directory
_config_path = Path(__file__).parent.parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("config", _config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
Config = config_module.Config

from .routes import router
from ..core.bootstrap import get_container

app = FastAPI(title="Obelisk Core API", version="0.1.0-alpha")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    # Build container and store in app.state for route access
    app.state.container = get_container(mode=Config.MODE)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Obelisk Core",
        "version": "0.1.0-alpha",
        "mode": Config.MODE,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": Config.MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)

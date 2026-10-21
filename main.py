import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers.api import router as api_router
from routers.ws import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High performance real-time AI English Speaker and Fluency Coach backend",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "endpoints": ["/api/scenarios", "/api/voices", "/api/chat", "/api/tts", "/ws/conversation"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

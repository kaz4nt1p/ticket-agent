import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import from new structure
from src.core.bot import app as bot_app
from src.services.price_tracker_scheduler import start_scheduler

load_dotenv()

app = FastAPI(title="Flight Tracker Bot API", version="1.0.0")

# Запуск шедулера при старте приложения
start_scheduler()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint для Docker
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "flytracker-bot"}

# Include the bot routes
app.include_router(bot_app, prefix="/tg")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

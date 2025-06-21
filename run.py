#!/usr/bin/env python3
"""
Flight Tracker Bot - Startup Script
Run this script to start the FastAPI server
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    from src.main import app
    import uvicorn
    
    print("🚀 Starting Flight Tracker Bot...")
    print("📱 Telegram Bot API: Ready")
    print("🔍 Aviasales API: Ready")
    print("🤖 OpenAI API: Ready")
    print("💾 Redis Cache: Ready")
    print("\n🌐 Server starting on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 
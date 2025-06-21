import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = "https://shiny-ideas-tickle.loca.lt/tg/webhook"

async def set_webhook():
    """Set the webhook URL for the Telegram bot"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found in environment variables")
        print("Please create a .env file with your TELEGRAM_TOKEN")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    data = {"url": WEBHOOK_URL}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            result = response.json()
            
            if result.get("ok"):
                print(f"✅ Webhook set successfully!")
                print(f"📡 Webhook URL: {WEBHOOK_URL}")
                print(f"📊 Response: {result}")
            else:
                print(f"❌ Failed to set webhook: {result}")
                
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")

async def get_webhook_info():
    """Get current webhook information"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found in environment variables")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            result = response.json()
            
            if result.get("ok"):
                webhook_info = result.get("result", {})
                print(f"📡 Current webhook URL: {webhook_info.get('url', 'Not set')}")
                print(f"📊 Webhook info: {webhook_info}")
            else:
                print(f"❌ Failed to get webhook info: {result}")
                
    except Exception as e:
        print(f"❌ Error getting webhook info: {e}")

if __name__ == "__main__":
    import asyncio
    
    print("🔧 Setting up Telegram webhook...")
    print(f"🎯 Target URL: {WEBHOOK_URL}")
    print()
    
    # First check current webhook info
    print("📋 Current webhook information:")
    asyncio.run(get_webhook_info())
    print()
    
    # Set the new webhook
    print("🔗 Setting new webhook...")
    asyncio.run(set_webhook())
    print()
    
    # Verify the webhook was set
    print("✅ Verifying webhook setup:")
    asyncio.run(get_webhook_info()) 
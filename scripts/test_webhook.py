import httpx
import asyncio

WEBHOOK_URL = "https://shiny-ideas-tickle.loca.lt/tg/webhook"

async def test_webhook():
    """Test if the webhook endpoint is accessible"""
    print(f"🧪 Testing webhook endpoint: {WEBHOOK_URL}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test GET request to see if the server is reachable
            response = await client.get(WEBHOOK_URL.replace("/webhook", "/"))
            print(f"✅ Server is reachable! Status: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        print("💡 Make sure your FastAPI server is running and localtunnel is active")

if __name__ == "__main__":
    asyncio.run(test_webhook()) 
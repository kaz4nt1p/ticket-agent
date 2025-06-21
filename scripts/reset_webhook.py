#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def reset_webhook():
    """Reset Telegram webhook"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN not found in .env file")
        return False
    
    webhook_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    
    try:
        response = requests.post(webhook_url)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook reset successfully")
            return True
        else:
            print(f"❌ Failed to reset webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error resetting webhook: {e}")
        return False

def get_webhook_info():
    """Get current webhook info"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN not found in .env file")
        return
    
    webhook_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_url)
        result = response.json()
        
        if result.get('ok'):
            info = result['result']
            print(f"📡 Current webhook: {info.get('url', 'Not set')}")
            print(f"📊 Pending updates: {info.get('pending_update_count', 0)}")
        else:
            print(f"❌ Failed to get webhook info: {result.get('description')}")
    except Exception as e:
        print(f"❌ Error getting webhook info: {e}")

if __name__ == "__main__":
    print("🔄 Resetting webhook...")
    reset_webhook()
    
    print("\n" + "="*50)
    get_webhook_info() 
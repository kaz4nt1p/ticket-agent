import asyncio
from openai_agent import extract_flight_query

async def test_conversation_flow():
    """Test the conversation flow with multiple messages"""
    
    print("🧪 Testing Conversation Flow...")
    print("=" * 60)
    
    # Simulate the conversation from the logs
    conversation = [
        "Москва Бангкок",
        "Вторая половина августа", 
        "Из москвы в бангкок",
        "на вторую половину августа"
    ]
    
    history = []
    
    for i, message in enumerate(conversation, 1):
        print(f"\n{i}. User: '{message}'")
        print(f"   History: {history}")
        
        try:
            result = await extract_flight_query(message, history=history)
            print(f"   Result: {result}")
            
            # Update history for next iteration
            history.append(message)
            
            # Check if we have complete parameters
            need_clarify = result.get("need_clarify", [])
            if need_clarify:
                print(f"   ⚠️  Still needs: {need_clarify}")
            else:
                print(f"   ✅ Complete query ready!")
                break
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Conversation flow test completed!")

if __name__ == "__main__":
    asyncio.run(test_conversation_flow()) 
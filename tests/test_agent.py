import asyncio
from openai_agent import extract_flight_query

async def test_agent():
    """Test the AI agent with various inputs"""
    test_cases = [
        "Москва Нячанг",
        "Билеты в Сочи",
        "Хочу в Бангкок завтра",
        "Москва Бали 15.08.2025 без пересадок",
        "есть ли билеты в Париж?"
    ]
    
    print("🧪 Testing AI Agent...")
    print("=" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{test_input}'")
        try:
            result = await extract_flight_query(test_input)
            print(f"   Result: {result}")
            
            # Check if clarification is needed
            need_clarify = result.get("need_clarify", [])
            if need_clarify:
                print(f"   ⚠️  Needs clarification: {need_clarify}")
            else:
                print(f"   ✅ Complete query")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_agent()) 
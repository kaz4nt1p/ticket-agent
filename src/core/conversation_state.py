import json
from typing import Dict, Optional, Any
from src.services.redis_client import redis_client

CONVERSATION_TTL = 60 * 60 * 24  # 1 день

class ConversationState:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.key = f"conversation_state:{chat_id}"
    
    def get_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        state_data = redis_client.get(self.key)
        if state_data:
            if isinstance(state_data, bytes):
                return json.loads(state_data.decode('utf-8'))
            elif isinstance(state_data, str):
                return json.loads(state_data)
        return {
            "from": None,
            "to": None,
            "date": None,
            "transfers": "any",
            "is_complete": False
        }
    
    def update_state(self, new_params: Dict[str, Any]):
        """Update conversation state with new parameters"""
        current_state = self.get_state()
        
        # Update only non-None values
        for key, value in new_params.items():
            if value is not None and value != "any":
                current_state[key] = value
        
        # Check if we have all required parameters
        current_state["is_complete"] = (
            current_state.get("from") is not None and 
            current_state.get("to") is not None and 
            current_state.get("date") is not None
        )
        
        # Save to Redis
        redis_client.setex(
            self.key, 
            CONVERSATION_TTL, 
            json.dumps(current_state)
        )
        
        return current_state
    
    def clear_state(self):
        """Clear conversation state"""
        redis_client.delete(self.key)
    
    def get_missing_params(self) -> list[str]:
        """Get list of missing parameters"""
        state = self.get_state()
        missing = []
        
        if not state.get("from"):
            missing.append("from")
        if not state.get("to"):
            missing.append("to")
        if not state.get("date"):
            missing.append("date")
        
        return missing

def get_conversation_state(chat_id: int) -> ConversationState:
    """Get conversation state for a chat"""
    return ConversationState(chat_id) 
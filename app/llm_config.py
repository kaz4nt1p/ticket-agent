import os
from langchain.chat_models import ChatOpenAI

def get_parser_llm():
    """Cheap JSON extractor"""
    return ChatOpenAI(
        model      = os.getenv("LLM_PARSER_MODEL", "gpt-3.5-turbo-1106"),
        temperature= 0,
        max_tokens = int(os.getenv("LLM_PARSER_MAXTOK", 300)),
    )

def get_dialog_llm():
    """Main reasoning model"""
    return ChatOpenAI(
        model      = os.getenv("LLM_DIALOG_MODEL", "gpt-4o"),
        temperature= 0.3,
        max_tokens = int(os.getenv("LLM_DIALOG_MAXTOK", 800)),
    )

import os
from app.llm_config import get_parser_llm, get_dialog_llm

def test_parser_llm_model():
    os.environ["LLM_PARSER_MODEL"] = "gpt-3.5-turbo-1106"
    llm = get_parser_llm()
    assert llm.model_name == "gpt-3.5-turbo-1106"

def test_dialog_llm_max_tokens():
    os.environ["LLM_DIALOG_MAXTOK"] = "800"
    llm = get_dialog_llm()
    assert llm.max_tokens == 800

from app.llm_config import get_dialog_llm
from tools.extract_params import ExtractParamsTool
from tools.flight_cache import FlightCacheTool
from tools.parse_cache import ParseCacheTool
from tools.aviasales_search import AviasalesSearchTool


def system_message():
    return (
        "1) Сначала пробуй parse_cache(query).\n"
        "2) Если вернулся null — extract_params() → сразу сохрани в parse_cache.\n"
        "3) Затем flight_cache → если нет, AviasalesSearchTool → сохранить flight_cache.\n"
        "4) Ответ ≤ 70 слов; если нет from/to/date — спроси недостающее."
    )


def get_agent():
    tools = [ParseCacheTool(), ExtractParamsTool(), FlightCacheTool(), AviasalesSearchTool()]
    llm = get_dialog_llm()
    sys_msg = system_message()
    return {"llm": llm, "tools": tools, "system_message": sys_msg}

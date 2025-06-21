from app.llm_config import get_parser_llm
from langchain.chains import LLMChain

class ExtractParamsTool:
    name = "ExtractParamsTool"
    description = "Извлекает параметры поиска из пользовательского запроса."

    def __init__(self):
        self.llm = get_parser_llm()
        self.chain = LLMChain(llm=self.llm, prompt=None)  # prompt задаётся отдельно

    def __call__(self, query, **kwargs):
        # Здесь должен быть ваш prompt для извлечения параметров
        prompt = kwargs.get("prompt")
        return self.chain.run(query, prompt=prompt)

# Примитивный кэш для парсинга параметров (можно заменить на Redis)
class ParseCacheTool:
    _cache = {}
    name = "ParseCacheTool"
    description = "Кэширует результаты парсинга параметров."

    def __call__(self, query):
        return self._cache.get(query)

    def save(self, query, params):
        self._cache[query] = params

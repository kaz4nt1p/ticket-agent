# Примитивный кэш для результатов поиска рейсов (можно заменить на Redis)
class FlightCacheTool:
    _cache = {}
    name = "FlightCacheTool"
    description = "Кэширует результаты поиска рейсов."

    def __call__(self, params):
        key = str(params)
        return self._cache.get(key)

    def save(self, params, flights):
        key = str(params)
        self._cache[key] = flights

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.services.flight_cache import flight_cache

class AviasalesSearchTool:
    """Поиск авиабилетов через Aviasales API с кэшированием"""
    
    def __init__(self):
        self.name = "AviasalesSearchTool"
        self.description = "Ищет авиабилеты через Aviasales API с кэшированием в Redis."
        self.api_token = os.getenv('AVIASALES_TOKEN')
        self.base_url = "https://api.aviasales.ru"
    
    def _get_iata_code(self, city_name: str) -> Optional[str]:
        """Получает IATA код города через API Aviasales"""
        try:
            url = f"{self.base_url}/places.json"
            params = {
                'term': city_name,
                'locale': 'ru',
                'types[]': 'city'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            places = response.json()
            if places and len(places) > 0:
                # Берем первый результат (самый релевантный)
                return places[0].get('code')
            
            return None
        except Exception as e:
            print(f"[IATA ERROR] Failed to get IATA code for {city_name}: {e}")
            return None
    
    def _search_flights(self, params: Dict[str, Any]) -> List[Dict]:
        """Выполняет поиск рейсов через API Aviasales"""
        try:
            # Подготавливаем параметры для API
            search_params = {
                'origin': params.get('from'),
                'destination': params.get('to'),
                'depart_date': params.get('date'),
                'currency': 'rub',
                'market': 'ru',
                'limit': 10
            }
            
            # Добавляем фильтр по пересадкам
            if params.get('transfers') == 0:
                search_params['direct'] = True
            
            url = f"{self.base_url}/v3/prices_for_dates"
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=search_params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            flights = data.get('data', [])
            
            # Форматируем результаты
            formatted_flights = []
            for flight in flights:
                formatted_flight = {
                    'flight_number': flight.get('flight_number', 'N/A'),
                    'airline': flight.get('airline', 'N/A'),
                    'origin_airport': flight.get('origin_airport'),
                    'destination_airport': flight.get('destination_airport'),
                    'departure_at': flight.get('departure_at'),
                    'price': flight.get('price'),
                    'transfers': flight.get('transfers', 0),
                    'duration': flight.get('duration'),
                    'link': flight.get('link')
                }
                formatted_flights.append(formatted_flight)
            
            print(f"[AVIASALES] Found {len(formatted_flights)} flights")
            return formatted_flights
            
        except Exception as e:
            print(f"[AVIASALES ERROR] Failed to search flights: {e}")
            return []
    
    def search(self, params: Dict[str, Any]) -> List[Dict]:
        """Поиск рейсов с кэшированием"""
        # Проверяем кэш
        cached_flights = flight_cache.get(params)
        if cached_flights:
            print(f"[CACHE HIT] Found {len(cached_flights)} cached flights")
            return cached_flights
        
        print(f"[CACHE MISS] No cached flights found, searching...")
        
        # Получаем IATA коды городов
        from_iata = self._get_iata_code(params.get('from', ''))
        to_iata = self._get_iata_code(params.get('to', ''))
        
        if not from_iata or not to_iata:
            print(f"[IATA ERROR] Failed to get IATA codes: {params.get('from')} -> {from_iata}, {params.get('to')} -> {to_iata}")
            return []
        
        # Обновляем параметры с IATA кодами
        search_params = params.copy()
        search_params['from'] = from_iata
        search_params['to'] = to_iata
        
        # Выполняем поиск
        flights = self._search_flights(search_params)
        
        # Сохраняем в кэш
        if flights:
            flight_cache.save(params, flights)
        
        return flights
    
    def __call__(self, params: Dict[str, Any]) -> List[Dict]:
        """Совместимость с интерфейсом агента"""
        return self.search(params)

# Глобальный экземпляр поисковика
aviasales_search = AviasalesSearchTool()

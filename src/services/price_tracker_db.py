import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading

DB_PATH = 'tracked_flights.db'

# Потокобезопасный доступ к БД
_db_lock = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracked_flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                from_city TEXT NOT NULL,
                to_city TEXT NOT NULL,
                date TEXT NOT NULL,
                flight_number TEXT NOT NULL,
                airline TEXT,
                departure_time TEXT,
                arrival_time TEXT,
                transfers INTEGER,
                current_price INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

def add_tracked_flights(chat_id: int, flights: List[Dict[str, Any]]):
    now = datetime.utcnow().isoformat()
    print(f"[SUBSCRIBE] Добавление новых рейсов в подписку для chat_id={chat_id}: {len(flights)} рейсов")
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        for flight in flights:
            print(f"[SUBSCRIBE] {flight}")
            cursor.execute('''
                INSERT INTO tracked_flights (
                    chat_id, from_city, to_city, date, flight_number, airline, departure_time, arrival_time, transfers, current_price, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chat_id,
                flight.get('from_city'),
                flight.get('to_city'),
                flight.get('date'),
                flight.get('flight_number'),
                flight.get('airline'),
                flight.get('departure_time'),
                flight.get('arrival_time'),
                flight.get('transfers'),
                flight.get('current_price'),
                now
            ))
        conn.commit()
        conn.close()

def get_tracked_flights() -> List[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tracked_flights')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

def get_tracked_flights_for_chat(chat_id: int) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tracked_flights WHERE chat_id = ?', (chat_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

def update_flight_price(flight_id: int, new_price: int):
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tracked_flights SET current_price = ? WHERE id = ?', (new_price, flight_id))
        conn.commit()
        conn.close()

def find_flight(chat_id: int, flight_number: str, date: str) -> Optional[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM tracked_flights WHERE chat_id = ? AND flight_number = ? AND date = ?
        ''', (chat_id, flight_number, date))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

# Инициализация БД при импорте
init_db() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET SEARCH — РАБОТА С БАЗОЙ ДАННЫХ

import sqlite3
import os
from datetime import datetime
from config import DB_PATH

def init_db():
    """Инициализация базы данных"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT, 
                  first_name TEXT,
                  vip_status INTEGER DEFAULT 0, 
                  vip_date TEXT,
                  search_count INTEGER DEFAULT 0, 
                  join_date TEXT)''')
    
    # Таблица поисков
    c.execute('''CREATE TABLE IF NOT EXISTS searches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  query TEXT,
                  result TEXT,
                  search_date TEXT,
                  source TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Таблица для базы утечек (2 ТБ)
    c.execute('''CREATE TABLE IF NOT EXISTS leaks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query TEXT,
                  data TEXT,
                  source TEXT,
                  added_date TEXT)''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    """Добавление нового пользователя"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO users (user_id, username, first_name, vip_status, join_date) VALUES (?, ?, ?, 0, ?)",
              (user_id, username or "Без юзернейма", first_name or "Unknown", now))
    conn.commit()
    conn.close()

def get_user(user_id):
    """Получение данных пользователя"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def set_vip(user_id):
    """Установка VIP статуса"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("UPDATE users SET vip_status = 1, vip_date = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

def add_search(user_id, query, result, source):
    """Сохранение результата поиска"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO searches (user_id, query, result, search_date, source) VALUES (?, ?, ?, ?, ?)",
              (user_id, query, result, datetime.now().isoformat(), source))
    c.execute("UPDATE users SET search_count = search_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_search_count(user_id):
    """Получение количества поисков"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT search_count FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def search_local_db(query):
    """Поиск в локальной базе данных (частичное совпадение)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Очищаем запрос от лишних символов
        clean_query = query.strip()
        
        # Ищем по всем полям с LIKE (частичное совпадение)
        c.execute("""
            SELECT data, source FROM leaks 
            WHERE query LIKE ? 
               OR data LIKE ? 
               OR data LIKE ?
               OR data LIKE ?
            ORDER BY added_date DESC LIMIT 20
        """, (
            f"%{clean_query}%",              # точное вхождение
            f"%{clean_query}%",              # в data
            f"%{clean_query.replace(' ', '%')}%",  # с пробелами как %
            f"%{clean_query[:10]}%"          # первые 10 символов
        ))
        
        results = c.fetchall()
        conn.close()
        
        # Если ничего не найдено — пробуем искать без спецсимволов
        if not results:
            import re
            clean = re.sub(r'[^a-zA-Z0-9а-яА-Я]', '', query)
            if len(clean) > 3:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                    SELECT data, source FROM leaks 
                    WHERE query LIKE ? OR data LIKE ?
                    ORDER BY added_date DESC LIMIT 10
                """, (f"%{clean}%", f"%{clean}%"))
                results = c.fetchall()
                conn.close()
        
        return results
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []

def get_db_stats():
    """Возвращает общее количество записей и добавленных за сегодня"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Всего записей
        c.execute("SELECT COUNT(*) FROM leaks")
        total = c.fetchone()[0]
        
        # Записей добавленных сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT COUNT(*) FROM leaks WHERE added_date LIKE ?", (today + '%',))
        added_today = c.fetchone()[0]
        
        conn.close()
        return total, added_today
    except:
        return 0, 0
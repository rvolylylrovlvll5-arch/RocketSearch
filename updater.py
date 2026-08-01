#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET SEARCH — ЕЖЕДНЕВНОЕ ОБНОВЛЕНИЕ БАЗЫ

import os
import sqlite3
import requests
import json
import shutil
from datetime import datetime
from config import DB_PATH, BACKUP_DIR

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_stats():
    """Получение статистики базы"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM leaks")
        count = c.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def backup_db():
    """Создание бэкапа базы данных"""
    if os.path.exists(DB_PATH):
        backup_name = f"{BACKUP_DIR}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(DB_PATH, backup_name)
        print(f"[+] Бэкап создан: {backup_name}")
        return backup_name
    return None

def add_leaks_from_file(file_path):
    """Добавление утечек из файла (CSV, JSON, TXT)"""
    if not os.path.exists(file_path):
        print(f"[-] Файл {file_path} не найден")
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    added = 0
    
    try:
        # Для JSON
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    query = item.get('query', '')
                    result = item.get('data', '') or item.get('result', '')
                    source = item.get('source', 'unknown')
                    c.execute("INSERT INTO leaks (query, data, source, added_date) VALUES (?, ?, ?, ?)",
                              (query, result, source, datetime.now().isoformat()))
                    added += 1
        
        # Для CSV (пример)
        elif file_path.endswith('.csv'):
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        query = row[0]
                        result = row[1]
                        source = row[2] if len(row) > 2 else 'csv'
                        c.execute("INSERT INTO leaks (query, data, source, added_date) VALUES (?, ?, ?, ?)",
                                  (query, result, source, datetime.now().isoformat()))
                        added += 1
        
        # Для TXT (каждая строка)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        query, result = line.split(':', 1)
                        c.execute("INSERT INTO leaks (query, data, source, added_date) VALUES (?, ?, ?, ?)",
                                  (query.strip(), result.strip(), 'txt', datetime.now().isoformat()))
                        added += 1
        
        conn.commit()
    except Exception as e:
        print(f"[-] Ошибка добавления данных: {e}")
    
    conn.close()
    return added

def update_db():
    """Обновление базы данных"""
    print(f"[{datetime.now()}] Начинаю обновление базы...")
    
    # Бэкап
    backup_db()
    
    old_total = get_db_stats()
    
    # Список файлов для загрузки
    data_dir = "data"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith(('.json', '.csv', '.txt'))]
        total_added = 0
        
        for file in files:
            file_path = os.path.join(data_dir, file)
            print(f"[*] Обработка {file}...")
            added = add_leaks_from_file(file_path)
            total_added += added
            print(f"[+] Добавлено {added} записей из {file}")
    
    new_total = get_db_stats()
    added_today = new_total - old_total
    
    # Сохраняем статистику
    with open('daily_stats.txt', 'w') as f:
        f.write(f"{new_total}\n{added_today}")
    
    print(f"[+] Всего добавлено: {added_today} записей")
    print(f"[+] Всего в базе: {new_total} записей")
    print(f"[{datetime.now()}] Обновление завершено!")

if __name__ == "__main__":
    update_db()
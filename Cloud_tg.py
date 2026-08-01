#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET CLOUD — ХРАНЕНИЕ ЛЮБЫХ ФАЙЛОВ В TELEGRAM

import os
import requests
import time
import glob

# ===== НАСТРОЙКИ =====
BOTS = {
    "bot1": "8942720260:AAHBkyficeUOPWCTG0fYk2dS9y3w7lpngkU",
    "bot2": "7995676128:AAEbvJX_CHtxjEhQC4vMnUaATMJPwOipkUM",
    "bot3": "8967498700:AAGA9eRboUOUNOSIzsi0GqNyuWeEXQrupZM",
    "bot4": "8704775048:AAHIRSczyzMF5axMyjYlPDWdRW3sH-dQSlA"
    # Добавь сколько нужно
}

CHAT_ID = "8119594441"  # Например, @username или -100123456789
DATA_DIR = "data"  # Папка с файлами

# ===== ЗАГРУЗКА ФАЙЛА =====
def upload_file_to_tg(bot_token, file_path, caption=""):
    """Загружает любой файл в Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    file_size = os.path.getsize(file_path) // (1024**2)
    file_name = os.path.basename(file_path)
    
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': CHAT_ID, 'caption': f'{caption} ({file_size} МБ)'}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        result = response.json()
        file_id = result['result']['document']['file_id']
        print(f"   ✅ {file_name} → {file_id[:20]}...")
        return file_id
    else:
        print(f"   ❌ Ошибка: {response.text}")
        return None

def upload_all_files():
    """Загружает все файлы из папки data/ во всех ботов"""
    files = []
    
    # Собираем все файлы
    for ext in ['*.db', '*.csv', '*.txt', '*.xlsx', '*.json']:
        files.extend(glob.glob(os.path.join(DATA_DIR, ext)))
    
    if not files:
        print("❌ Нет файлов для загрузки в папке data/")
        return
    
    print(f"[*] Найдено файлов: {len(files)}")
    
    for bot_name, bot_token in BOTS.items():
        print(f"\n📤 Загрузка в {bot_name}...")
        for file_path in files:
            file_name = os.path.basename(file_path)
            upload_file_to_tg(bot_token, file_path, f"📁 {file_name}")
            time.sleep(1)
    
    print(f"\n✅ Все файлы загружены в {len(BOTS)} ботов!")

# ===== СКАЧИВАНИЕ ФАЙЛА =====
def download_file_from_tg(bot_token, file_id, dest_path):
    """Скачивает файл из Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(url).json()
    
    if not response.get('ok'):
        print(f"❌ Ошибка: {response}")
        return False
    
    file_path = response['result']['file_path']
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    response = requests.get(file_url, stream=True)
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    
    print(f"✅ Скачано: {dest_path} ({os.path.getsize(dest_path) // (1024**2)} МБ)")
    return True

def get_file_id(bot_token, file_name):
    """Получает file_id для последнего загруженного файла"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url).json()
    
    if not response.get('ok'):
        return None
    
    for update in response.get('result', []):
        if 'message' in update and 'document' in update['message']:
            doc = update['message']['document']
            if doc.get('file_name') == file_name:
                return doc['file_id']
    return None

def list_files(bot_token):
    """Показывает все загруженные файлы"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url).json()
    
    if not response.get('ok'):
        return []
    
    files = []
    for update in response.get('result', []):
        if 'message' in update and 'document' in update['message']:
            doc = update['message']['document']
            files.append({
                'name': doc.get('file_name'),
                'size': doc.get('file_size') // (1024**2),
                'file_id': doc.get('file_id')
            })
    return files

# ===== МЕНЮ =====
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*50)
    print("  ☁️ ROCKET CLOUD — TELEGRAM ХРАНИЛИЩЕ")
    print("="*50)
    print(f"\n📁 Ботов: {len(BOTS)}")
    print(f"📁 Папка: {DATA_DIR}/")
    
    # Считаем файлы
    files = []
    for ext in ['*.db', '*.csv', '*.txt', '*.xlsx', '*.json']:
        files.extend(glob.glob(os.path.join(DATA_DIR, ext)))
    print(f"📁 Файлов для загрузки: {len(files)}")
    
    print("\n📌 Выберите действие:")
    print("[1] Загрузить ВСЕ файлы из data/ во всех ботов")
    print("[2] Загрузить только .csv и .txt")
    print("[3] Загрузить только .db (базу данных)")
    print("[4] Скачать файл по file_id")
    print("[5] Список файлов в боте")
    print("[6] Выход")
    
    choice = input("\nВыберите: ")
    
    if choice == '1':
        upload_all_files()
    
    elif choice == '2':
        files = glob.glob(os.path.join(DATA_DIR, '*.csv')) + glob.glob(os.path.join(DATA_DIR, '*.txt'))
        if not files:
            print("❌ Нет .csv или .txt файлов")
            return
        for bot_name, bot_token in BOTS.items():
            print(f"\n📤 Загрузка в {bot_name}...")
            for file_path in files:
                upload_file_to_tg(bot_token, file_path, f"📁 {os.path.basename(file_path)}")
                time.sleep(1)
    
    elif choice == '3':
        db_path = os.path.join(DATA_DIR, 'databases.db')
        if not os.path.exists(db_path):
            print("❌ База не найдена")
            return
        for bot_name, bot_token in BOTS.items():
            print(f"\n📤 Загрузка в {bot_name}...")
            upload_file_to_tg(bot_token, db_path, "🗄️ База данных RocketSearch")
            time.sleep(1)
    
    elif choice == '4':
        bot_name = input("Имя бота (bot1, bot2...): ")
        if bot_name not in BOTS:
            print(f"❌ Бот {bot_name} не найден")
            return
        file_id = input("Введите file_id: ")
        dest = input("Куда сохранить? (например, data/file.csv): ")
        download_file_from_tg(BOTS[bot_name], file_id, dest)
    
    elif choice == '5':
        bot_name = input("Имя бота (bot1, bot2...): ")
        if bot_name not in BOTS:
            print(f"❌ Бот {bot_name} не найден")
            return
        files = list_files(BOTS[bot_name])
        if files:
            print("\n📁 Файлы в боте:")
            for f in files:
                print(f"   • {f['name']} ({f['size']} МБ) → {f['file_id'][:30]}...")
        else:
            print("❌ Нет файлов")

if __name__ == "__main__":
    main()
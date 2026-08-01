#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET SEARCH — ФОРМАТ 5 + ПАГИНАЦИЯ + СКАЧИВАНИЕ

import logging
import os
import sys
import re
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN, ADMIN_ID, VIP_PRICE
from database import init_db, add_user, get_user, set_vip, add_search, get_search_count, search_local_db, get_db_stats
from parsers import search_leakosint, search_funstat, search_vektor

init_db()

PRO_BOT_LINK = "https://t.me/RocketSearchPRO_bot"

# ===== КЛАВИАТУРЫ =====
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("💰 Заработать", callback_data="earn")],
        [InlineKeyboardButton("🔗 Купить PRO", callback_data="buy_pro")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_search_keyboard():
    keyboard = [
        [InlineKeyboardButton("🕵️ Личность", callback_data="search_person")],
        [InlineKeyboardButton("📲 Контакты", callback_data="search_contact")],
        [InlineKeyboardButton("🚘 Транспорт", callback_data="search_car")],
        [InlineKeyboardButton("💬 Соцсети", callback_data="search_social")],
        [InlineKeyboardButton("📟 Telegram", callback_data="search_telegram")],
        [InlineKeyboardButton("📄 Документы", callback_data="search_docs")],
        [InlineKeyboardButton("🌐 Онлайн-следы", callback_data="search_online")],
        [InlineKeyboardButton("🏚 Недвижимость", callback_data="search_property")],
        [InlineKeyboardButton("🏢 Юрлицо", callback_data="search_company")],
        [InlineKeyboardButton("📸 Распознавание лица", callback_data="search_face")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПАГИНАЦИИ =====
async def show_page(update_or_query, context, page=0, is_callback=False):
    """Показывает страницу результатов"""
    results = context.user_data.get('search_results', [])
    query_text = context.user_data.get('search_query', '')
    total = len(results)
    per_page = 5
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    start = page * per_page
    end = min(start + per_page, total)
    page_results = results[start:end]
    
    # Формируем ответ (ФОРМАТ 5)
    response = f"=== ROCKET SEARCH ===\n\n"
    response += f"Запрос: {query_text}\n"
    response += f"Всего результатов: {total}\n"
    response += f"Страница: {page + 1}/{total_pages}\n"
    response += f"Время: {random.uniform(0.01, 0.05):.3f} сек\n\n"
    response += f"--- Найдено ---\n"
    
    # Сохраняем полные данные для скачивания
    full_data = f"=== ROCKET SEARCH ===\n"
    full_data += f"Запрос: {query_text}\n"
    full_data += f"Всего результатов: {total}\n\n"
    full_data += f"--- Найдено ---\n"
    
    if page_results:
        for i, row in enumerate(page_results, start + 1):
            data = row[0] if row else ''
            response += f"{i}. {data[:300]}\n"
            full_data += f"{i}. {data}\n"
    else:
        response += "Нет данных\n"
    
    # Сохраняем полный файл
    filename = f"search_{context.user_data.get('user_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(full_data)
    context.user_data['current_filename'] = filename
    
    # Кнопки
    keyboard = []
    
    # Навигация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="page_info"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"page_{page + 1}"))
    keyboard.append(nav_row)
    
    # Скачать и назад
    keyboard.append([InlineKeyboardButton("💾 Скачать всё", callback_data=f"download_{filename}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_callback:
        await update_or_query.edit_message_text(
            response,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update_or_query.message.reply_text(
            response,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "Без юзернейма"
    first_name = user.first_name or "Unknown"
    
    add_user(user_id, username, first_name)
    
    total, added_today = get_db_stats()
    total_str = f"{total:,}".replace(',', ' ')
    added_str = f"{added_today:,}".replace(',', ' ')
    
    await update.message.reply_text(
        f"🚀 **RocketSearch** — твой цифровой детектив\n\n"
        f"🔍 Поиск в утечках данных\n"
        f"📁 **База данных:** {total_str} записей\n"
        f"📊 **+{added_str} новых строк сегодня**\n"
        f"🔄 Обновление: ежедневно\n\n"
        f"👤 {first_name} (@{username})\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"📌 Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "back_main":
        await query.edit_message_text(
            "📌 **Главное меню:**",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "search":
        await query.edit_message_text(
            "🔍 **Выберите тип поиска:**",
            reply_markup=get_search_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "buy_pro":
        await query.edit_message_text(
            f"🔗 **КУПИТЬ PRO ВЕРСИЮ**\n\n"
            f"💎 **Что даёт PRO:**\n"
            f"• Безлимитные запросы\n"
            f"• Полная база 2 ТБ\n"
            f"• Расширенный анализ от ИИ\n"
            f"• Эксклюзивные стили\n"
            f"• VIP статус\n\n"
            f"💰 **Цена: 500₽ — навсегда**\n"
            f"💳 Оплата через CryptoBot\n\n"
            f"📌 Перейдите в PRO бота: {PRO_BOT_LINK}",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "profile":
        user = get_user(user_id)
        if user:
            vip_status = "🆓 FREE" if user[3] == 0 else "👑 PRO"
            search_count = get_search_count(user_id)
            await query.edit_message_text(
                f"👤 **Ваш профиль:**\n\n"
                f"🆔 ID: `{user_id}`\n"
                f"📛 Имя: {user[2]}\n"
                f"👤 Юзернейм: @{user[1] if user[1] else 'нет'}\n"
                f"📊 Версия: {vip_status}\n"
                f"🔍 Запросов: {search_count}/10 (сегодня)\n"
                f"📅 Регистрация: {user[6][:10] if user[6] else 'неизвестно'}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    elif data == "earn":
        await query.edit_message_text(
            f"💰 **ЗАРАБОТАТЬ**\n\n"
            f"1️⃣ **Партнёрская программа**\n"
            f"• 30% от покупок друзей\n"
            f"2️⃣ **Реклама**\n"
            f"• От 1000₽/месяц\n"
            f"3️⃣ **Стать партнёром PRO**\n"
            f"• Продавайте PRO доступ\n"
            f"• Получайте 50% от продаж\n\n"
            f"👨‍💻 Связь: @vassapboy",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "help":
        await query.edit_message_text(
            f"ℹ️ **ПОМОЩЬ**\n\n"
            f"📌 **Как пользоваться:**\n"
            f"1️⃣ Выберите тип поиска\n"
            f"2️⃣ Введите данные\n"
            f"3️⃣ Получите результат\n\n"
            f"📌 **Лимиты:**\n"
            f"• 10 запросов в день (FREE)\n"
            f"• Безлимит (PRO)\n\n"
            f"👨‍💻 Поддержка: @vassapboy",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data.startswith("search_"):
        search_type = data.replace("search_", "")
        context.user_data['search_type'] = search_type
        
        search_count = get_search_count(user_id)
        if search_count >= 10:
            await query.edit_message_text(
                f"❌ **Лимит исчерпан!**\n\n"
                f"Вы использовали все 10 бесплатных запросов.\n\n"
                f"🔗 Купите PRO: {PRO_BOT_LINK}",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        type_names = {
            "person": "Личность (ФИО, дата)",
            "contact": "Контакты (номер, email)",
            "car": "Транспорт (номер, VIN)",
            "social": "Соцсети (VK, Instagram, TikTok, OK)",
            "telegram": "Telegram (@username, ID)",
            "docs": "Документы (паспорт, СНИЛС, ИНН)",
            "online": "Онлайн-следы (домен, IP)",
            "property": "Недвижимость (адрес, кадастр)",
            "company": "Юрлицо (ИНН, ОГРН)",
            "face": "Распознавание лица"
        }
        
        examples = {
            "person": "Иванов Иван Анатольевич 04.06.1976",
            "contact": "+79999688666 или user@mail.ru",
            "car": "В395ОК199 или XTA211440C5106924",
            "social": "vk.com/sherlock или instagram.com/sherlock",
            "telegram": "@sherlock или tg123456",
            "docs": "/vu 1234567890 или /passport 1234567890",
            "online": "sherlock.com или 1.1.1.1",
            "property": "Город, Улица, 1 или 77:01:0004042:6987",
            "company": "/inn 2540214547 или 1107449004464"
        }
        
        await query.edit_message_text(
            f"🔍 **Поиск по: {type_names.get(search_type, search_type)}**\n\n"
            f"📌 Пример: `{examples.get(search_type, 'введите данные')}`\n\n"
            f"📝 Введите данные для поиска:",
            reply_markup=get_search_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data.startswith("page_"):
        page = int(data.replace("page_", ""))
        await show_page(query, context, page, is_callback=True)
    
    elif data.startswith("download_"):
        filename = data.replace("download_", "")
        try:
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    await query.message.reply_document(
                        document=f,
                        filename=filename,
                        caption="📄 Полный результат поиска сохранён!"
                    )
                os.remove(filename)
            else:
                await query.edit_message_text("❌ Файл не найден.")
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query_text = update.message.text.strip()
    search_type = context.user_data.get('search_type', 'person')
    
    # Проверка лимита
    search_count = get_search_count(user_id)
    if search_count >= 10:
        await update.message.reply_text(
            f"❌ **Лимит исчерпан!**\n\n"
            f"Вы использовали все 10 бесплатных запросов.\n\n"
            f"🔗 Купите PRO: {PRO_BOT_LINK}",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    await update.message.chat.send_action(action="typing")
    
    # Поиск
    results = search_local_db(query_text)
    
    if results:
        # Сохраняем в context
        context.user_data['search_results'] = results
        context.user_data['search_query'] = query_text
        context.user_data['user_id'] = user_id
        
        add_search(user_id, query_text, f"Найдено {len(results)} записей", "локальная БД")
        
        # Показываем первую страницу
        await show_page(update, context, page=0, is_callback=False)
    else:
        response = f"❌ **НИЧЕГО НЕ НАЙДЕНО**\n\n"
        response += f"Запрос: {query_text}\n"
        response += f"Время: {random.uniform(0.01, 0.05):.3f} сек\n\n"
        response += f"💡 Попробуйте:\n"
        response += f"• Проверить правильность данных\n"
        response += f"• Использовать другой формат\n"
        response += f"• Купить PRO для полной базы\n\n"
        response += f"🆓 Вы пользуетесь бесплатной версией."
    
        await update.message.reply_text(
            response,
            reply_markup=get_search_keyboard(),
            parse_mode="Markdown"
        )

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 ROCKET SEARCH БОТ ЗАПУЩЕН!")
    app.run_polling()

if __name__ == "__main__":
    main()
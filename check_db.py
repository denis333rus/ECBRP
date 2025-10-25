#!/usr/bin/env python3
"""
Скрипт для проверки и обновления базы данных
"""

import sqlite3
import os

def check_database():
    """Проверяем структуру базы данных"""
    if not os.path.exists('news.db'):
        print("❌ База данных не найдена")
        return False
    
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('PRAGMA table_info(news)')
        columns = cursor.fetchall()
        
        print("📊 Структура таблицы news:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Проверяем наличие нужных колонок
        column_names = [col[1] for col in columns]
        
        if 'attachment_filename' not in column_names:
            print("⚠️ Колонка attachment_filename отсутствует")
            cursor.execute('ALTER TABLE news ADD COLUMN attachment_filename TEXT')
            print("✅ Колонка attachment_filename добавлена")
        
        if 'attachment_original_name' not in column_names:
            print("⚠️ Колонка attachment_original_name отсутствует")
            cursor.execute('ALTER TABLE news ADD COLUMN attachment_original_name TEXT')
            print("✅ Колонка attachment_original_name добавлена")
        
        conn.commit()
        print("✅ База данных обновлена успешно!")
        
        # Проверяем количество записей
        cursor.execute('SELECT COUNT(*) FROM news')
        count = cursor.fetchone()[0]
        print(f"📰 Всего новостей в базе: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Проверка базы данных...")
    check_database()

#!/usr/bin/env python3
"""
Скрипт для инициализации PostgreSQL базы данных
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def create_database():
    """Создает базу данных если она не существует"""
    
    # Параметры подключения к PostgreSQL
    db_host = os.getenv('DB_HOST', '217.196.101.222')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'slon')
    db_password = os.getenv('DB_PASSWORD', 'jojo2402')
    db_name = os.getenv('DB_NAME', 'autodeploy_db')
    
    try:
        # Подключаемся к PostgreSQL серверу (не к конкретной базе данных)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'  # Подключаемся к системной базе postgres
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем, существует ли база данных
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Создаю базу данных '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"База данных '{db_name}' успешно создана!")
        else:
            print(f"База данных '{db_name}' уже существует.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return False

def test_connection():
    """Тестирует подключение к базе данных"""
    
    db_host = os.getenv('DB_HOST', '217.196.101.222')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'slon')
    db_password = os.getenv('DB_PASSWORD', 'jojo2402')
    db_name = os.getenv('DB_NAME', 'autodeploy_db')
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        
        print(f"Подключение к PostgreSQL успешно!")
        print(f"Версия PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return False

if __name__ == "__main__":
    print("=== Инициализация PostgreSQL базы данных ===")
    
    # Создаем базу данных
    if create_database():
        # Тестируем подключение
        test_connection()
    else:
        print("Не удалось создать базу данных. Проверьте параметры подключения.")
        sys.exit(1) 
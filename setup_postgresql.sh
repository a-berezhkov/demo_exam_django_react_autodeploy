#!/bin/bash

echo "=== Настройка PostgreSQL для Django проекта ==="

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не установлен"
    exit 1
fi

# Проверяем наличие pip
if ! command -v pip &> /dev/null; then
    echo "Ошибка: pip не установлен"
    exit 1
fi

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install -r requirements.txt

# Создаем файл .env если его нет
if [ ! -f .env ]; then
    echo "Создаем файл .env..."
    cat > .env << EOF
# Database Configuration
DB_HOST=217.196.101.222
DB_PORT=5432
DB_NAME=autodeploy_db
DB_USER=slon
DB_PASSWORD=jojo2402

# Django Configuration
SECRET_KEY=django-insecure-_b=^4%h6#1p31s1j!g7j7$!46neao8ue$vg8&tt!8d+1ci0!gz
DEBUG=True
ALLOWED_HOSTS=83.217.220.94,localhost,127.0.0.1,5141353-cf45690,217.196.101.222
EOF
    echo "Файл .env создан"
else
    echo "Файл .env уже существует"
fi

# Инициализируем базу данных
echo "Инициализируем базу данных PostgreSQL..."
python init_db.py

if [ $? -eq 0 ]; then
    echo "База данных инициализирована успешно"
else
    echo "Ошибка при инициализации базы данных"
    exit 1
fi

# Мигрируем данные из SQLite если есть
if [ -f db.sqlite3 ]; then
    echo "Найден файл SQLite. Мигрируем данные..."
    python migrate_to_postgres.py
    if [ $? -eq 0 ]; then
        echo "Данные мигрированы успешно"
    else
        echo "Ошибка при миграции данных"
    fi
else
    echo "Файл SQLite не найден. Пропускаем миграцию."
fi

# Выполняем миграции Django
echo "Выполняем миграции Django..."
python manage.py makemigrations
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "Миграции выполнены успешно"
else
    echo "Ошибка при выполнении миграций"
    exit 1
fi

# Создаем суперпользователя
echo "Создаем суперпользователя..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com

if [ $? -eq 0 ]; then
    echo "Суперпользователь создан: admin/admin"
else
    echo "Ошибка при создании суперпользователя"
fi

echo "=== Настройка завершена! ==="
echo "Для запуска сервера выполните: python manage.py runserver"
echo "Логин администратора: admin"
echo "Пароль: admin" 
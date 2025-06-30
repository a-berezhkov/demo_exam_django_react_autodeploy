# Настройка PostgreSQL для Django проекта

## 1. Установка зависимостей

```bash
# Установите новые зависимости
pip install -r requirements.txt
```

## 2. Создание файла .env

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Database Configuration
DB_HOST=217.196.101.222
DB_PORT=5432
DB_NAME=autodeploy_db
DB_USER= 
DB_PASSWORD= 

# Django Configuration
SECRET_KEY= 
DEBUG=True
 
```

## 3. Инициализация базы данных

```bash
# Создайте базу данных PostgreSQL
python init_db.py
```

## 4. Миграция данных из SQLite (если есть)

```bash
# Если у вас есть данные в SQLite, мигрируйте их в PostgreSQL
python migrate_to_postgres.py
```

## 5. Выполнение миграций Django

```bash
# Создайте и примените миграции
python manage.py makemigrations
python manage.py migrate
```

## 6. Создание суперпользователя

```bash
# Создайте администратора
python manage.py createsuperuser
```

## 7. Запуск сервера

```bash
# Запустите Django сервер
python manage.py runserver
```

## Проверка подключения

Для проверки подключения к PostgreSQL выполните:

```bash
python -c "
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    print('Подключение к PostgreSQL успешно!')
    conn.close()
except Exception as e:
    print(f'Ошибка подключения: {e}')
"
```

## Устранение проблем

### Ошибка подключения к PostgreSQL

1. Проверьте, что PostgreSQL сервер запущен
2. Убедитесь, что порт 5432 открыт
3. Проверьте правильность учетных данных в файле .env

### Ошибка "database does not exist"

Выполните скрипт инициализации:
```bash
python init_db.py
```

### Ошибка миграций

Удалите старые миграции и создайте новые:
```bash
rm -rf autodeploy/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

## Безопасность

- Никогда не коммитьте файл .env в Git
- Используйте сильные пароли в продакшене
- Ограничьте доступ к базе данных по IP адресам
- Регулярно делайте резервные копии базы данных 
# Автоматическое развертывание студенческих проектов на Django

## Оглавление

- [Автоматическое развертывание студенческих проектов на Django](#автоматическое-развертывание-студенческих-проектов-на-django)
  - [Оглавление](#оглавление)
  - [Описание](#описание)
  - [Требования](#требования)
  - [Установка и запуск локально](#установка-и-запуск-локально)
  - [Требования к архиву для загрузки](#требования-к-архиву-для-загрузки)
  - [Пример .env для frontend](#пример-env-для-frontend)
  - [Запуск на удалённом сервере по SSH](#запуск-на-удалённом-сервере-по-ssh)
  - [Управление проектами](#управление-проектами)
  - [Возможные проблемы и решения](#возможные-проблемы-и-решения)
  - [Примеры команд](#примеры-команд)
    - [Клонирование и запуск локально](#клонирование-и-запуск-локально)
    - [Запуск на сервере по SSH](#запуск-на-сервере-по-ssh)
  - [Контакты](#контакты)

---

## Описание

- **Backend:** Django + DRF (интерфейс на Django-шаблонах)
- **База данных:** SQLite
- **Docker:** для запуска проектов студентов (backend на DRF + frontend на React)
- **Reverse Proxy:** локально — прямые порты, для удалённого сервера — настройка Nginx (см. ниже)
- **Архивы:** хранятся локально

---

## Требования

- Python 3.10+
- Docker и Docker Compose
- Git
- pip

---

## Установка и запуск локально

1. **Клонируйте репозиторий:**
   ```bash
   git clone <URL_РЕПОЗИТОРИЯ>
   cd demo_exam
   ```

2. **Создайте и активируйте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Выполните миграции:**
   ```bash
   python manage.py migrate
   ```

5. **Запустите сервер Django:**
   ```bash
   python manage.py runserver
   ```

6. **Откройте в браузере:**
   ```
   http://localhost:8000/
   ```

---

## Требования к архиву для загрузки

- **Формат архива:** .zip, .tar, .tar.gz
- **Структура архива:**

  Пример 1 (рекомендуется):
  ```
  project_name.zip
  ├── frontend/
  │   ├── package.json
  │   ├── vite.config.js
  │   └── ...
  └── backend/
      ├── manage.py
      ├── requirements.txt
      └── ...
  ```
  Пример 2 (допустимо):
  ```
  project_name.zip
  └── my_folder/
      ├── frontend/
      └── backend/
  ```

- **frontend:** должен быть полноценным проектом на React/Vite (npm install, npm run dev должны работать)
- **backend:** должен быть полноценным Django-проектом (manage.py, requirements.txt)
- **Внутри frontend должен использоваться адрес API из переменной окружения VITE_URL** (например, process.env.VITE_URL).
- **Не должно быть конфликтов портов** — система сама назначает уникальные порты для каждого проекта.

---

## Пример .env для frontend

```
VITE_URL=http://localhost:8100/api/
```

---

## Запуск на удалённом сервере по SSH

1. **Подключитесь к серверу по SSH:**
   ```bash
   ssh <user>@<host>
   ```

2. **Установите Docker и Docker Compose (если не установлены):**
   - [Инструкция для Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
   - [Инструкция для Docker Compose](https://docs.docker.com/compose/install/)

3. **Установите Python, pip, git (если не установлены):**
   ```bash
   sudo apt update
   sudo apt install python3 python3-venv python3-pip git
   ```

4. **Клонируйте репозиторий и выполните шаги из раздела "Установка и запуск локально"** (см. выше).

5. **Откройте порт(ы) на сервере (например, 8000, 3100, 8100 и т.д.) в настройках firewall/ufw:**
   ```bash
   sudo ufw allow 8000
   sudo ufw allow 3100:3200/tcp
   sudo ufw allow 8100:8200/tcp
   ```

6. **(Рекомендуется) Настройте Nginx как reverse proxy для единой точки входа:**

   Пример nginx-конфига:
   ```nginx
   server {
       listen 80;
       server_name <your_domain_or_ip>;

       location / {
           proxy_pass http://localhost:<frontend_port>/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /api/ {
           proxy_pass http://localhost:<backend_port>/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   После изменения конфига перезапустите nginx:
   ```bash
   sudo systemctl restart nginx
   ```

7. **Загрузите архив через веб-интерфейс** — система сама развернёт контейнеры и выдаст ссылки.

---

## Управление проектами

- В интерфейсе Django отображаются все загруженные проекты.
- Для каждого проекта видны:
  - ФИО студента
  - Группа
  - Ссылки на frontend и backend (уникальные порты)
  - Статус контейнеров
  - Кнопки для запуска, остановки, удаления контейнеров (если реализовано)

---

## Возможные проблемы и решения

- **Порт уже занят:** система автоматически ищет свободный порт, но если портов не хватает — освободите их или увеличьте диапазон.
- **Docker не запускается:** проверьте, что Docker и Docker Compose установлены и запущены (`sudo systemctl status docker`).
- **Ошибка при сборке контейнера:** проверьте структуру архива и наличие всех нужных файлов (package.json, manage.py и т.д.).
- **Nginx не проксирует:** проверьте конфиг и перезапустите nginx.

---

## Примеры команд

### Клонирование и запуск локально
```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd demo_exam
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Запуск на сервере по SSH
```bash
ssh user@host
sudo apt update
sudo apt install python3 python3-venv python3-pip git docker.io docker-compose -y
git clone <URL_РЕПОЗИТОРИЯ>
cd demo_exam
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

---

## Контакты

Для вопросов и поддержки — пишите [ваш email или Telegram]. 
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
  - [Важно для запуска на сервере](#важно-для-запуска-на-сервере)
    - [Требования к Docker](#требования-к-docker)
    - [Как установить buildx и docker-compose (Ubuntu)](#как-установить-buildx-и-docker-compose-ubuntu)
    - [Как избежать лимита Docker Hub](#как-избежать-лимита-docker-hub)
    - [Что делать при ошибке legacy builder](#что-делать-при-ошибке-legacy-builder)
    - [Полезные ссылки](#полезные-ссылки)
  - [Особенности автодеплоя](#особенности-автодеплоя)
  - [Как запускать процессы, чтобы они не завершались после разрыва SSH](#как-запускать-процессы-чтобы-они-не-завершались-после-разрыва-ssh)

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
python manage.py runserver 0.0.0.0:80
```

---

## Контакты

Для вопросов и поддержки — пишите [ваш email или Telegram]. 

---

## Важно для запуска на сервере

### Требования к Docker
- Docker должен поддерживать buildx и buildkit (современная сборка образов)
- Должен быть установлен docker-compose (или docker compose)

### Как установить buildx и docker-compose (Ubuntu)

```bash
sudo apt update
sudo apt install docker-buildx-plugin docker-compose
```

Проверьте, что buildx установлен:
```bash
docker buildx version
```

Если команда не найдена — следуйте официальной инструкции: https://docs.docker.com/go/buildx/

### Как избежать лимита Docker Hub

Docker Hub ограничивает количество скачиваний образов для неавторизованных пользователей. Чтобы избежать ошибки:

```
toomanyrequests: You have reached your unauthenticated pull rate limit.
```

**Выполните на сервере:**
```bash
docker login -u <ваш_логин>
```
Введите свой логин и пароль от Docker Hub. Если нет аккаунта — зарегистрируйтесь на https://hub.docker.com/

### Что делать при ошибке legacy builder

Если видите ошибку:
```
DEPRECATED: The legacy builder is deprecated and will be removed in a future release. Install the buildx component to build images with BuildKit: https://docs.docker.com/go/buildx/
```

- Установите buildx (см. выше)
- После этого Docker будет использовать современный BuildKit для сборки образов

### Полезные ссылки
- [Docker Buildx (официальная документация)](https://docs.docker.com/go/buildx/)
- [Docker Compose (официальная документация)](https://docs.docker.com/compose/install/)
- [Docker Hub](https://hub.docker.com/) 

---

## Особенности автодеплоя

- При загрузке и запуске архива проекта внешний IP сервера (например, 83.217.220.94) автоматически добавляется в ALLOWED_HOSTS файла settings.py внутри backend-проекта.
- Это предотвращает ошибку DisallowedHost при обращении к backend по IP/порту.
- Вам НЕ нужно вручную менять ALLOWED_HOSTS в settings.py — всё делается автоматически.
- Если в settings.py уже есть ALLOWED_HOSTS, он будет заменён на нужный список: ['IP', 'localhost', '127.0.0.1'].
- Если ALLOWED_HOSTS отсутствует, он будет добавлен в конец файла. 

---

## Как запускать процессы, чтобы они не завершались после разрыва SSH

- Если используешь **docker-compose**, всегда запускай контейнеры с флагом `-d` (detached mode):
  ```bash
  docker-compose up -d
  ```
  Контейнеры будут работать в фоне и не закроются после выхода из SSH.

- Если запускаешь обычные серверы или скрипты вручную, используй:
  - **nohup**:
    ```bash
    nohup python manage.py runserver 0.0.0.0:8000 &
    ```
    Процесс продолжит работать после выхода из SSH.
  - **tmux** (или **screen**) — терминальный мультиплексор:
    ```bash
    # Просмотр существующих сессий
    tmux list-sessions
    # или сокращенно:
    tmux ls
    
    # Подключение к существующей сессии
    tmux attach-session -t имя_сессии
    # или сокращенно:
    tmux a -t имя_сессии
    
    # Создание новой сессии
    tmux new-session -s имя_сессии
    # или сокращенно:
    tmux new -s имя_сессии
    
    # внутри tmux запускаешь свой сервер
    python manage.py runserver 0.0.0.0:8000
    # чтобы отсоединиться: Ctrl+B, затем D
    ```
    Позволяет отсоединяться и возвращаться к сессии в любой момент.

- Для большинства задач с автодеплоем и docker-compose ничего дополнительно делать не нужно — контейнеры не зависят от SSH-сессии. 
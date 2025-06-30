#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в PostgreSQL
"""
import os
import sys
import django
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.db import connections
from autodeploy.models import Student, Group, ProjectUpload

def migrate_data():
    """Мигрирует данные из SQLite в PostgreSQL"""
    
    print("=== Миграция данных из SQLite в PostgreSQL ===")
    
    try:
        # Проверяем подключение к PostgreSQL
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Подключение к PostgreSQL успешно: {version[0]}")
        
        # Проверяем, есть ли данные в PostgreSQL
        if Student.objects.exists():
            print("Данные уже существуют в PostgreSQL. Миграция не требуется.")
            return True
        
        # Проверяем, есть ли SQLite файл
        sqlite_path = 'db.sqlite3'
        if not os.path.exists(sqlite_path):
            print("SQLite файл не найден. Миграция не требуется.")
            return True
        
        print("Начинаю миграцию данных...")
        
        # Временно переключаемся на SQLite
        from django.conf import settings
        original_db = settings.DATABASES['default']
        
        # Создаем временную конфигурацию для SQLite
        settings.DATABASES['sqlite'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
        
        # Импортируем модели для SQLite
        from django.apps import apps
        apps.clear_cache()
        
        # Читаем данные из SQLite
        with connections['sqlite'].cursor() as cursor:
            # Читаем группы
            cursor.execute("SELECT id, name FROM autodeploy_group")
            groups_data = cursor.fetchall()
            
            # Читаем студентов
            cursor.execute("SELECT id, full_name, group_id FROM autodeploy_student")
            students_data = cursor.fetchall()
            
            # Читаем проекты
            cursor.execute("""
                SELECT id, student_id, archive, uploaded_at, status, 
                       backend_port, frontend_port, backend_url, frontend_url,
                       container_id_backend, container_id_frontend
                FROM autodeploy_projectupload
            """)
            projects_data = cursor.fetchall()
        
        print(f"Найдено в SQLite: {len(groups_data)} групп, {len(students_data)} студентов, {len(projects_data)} проектов")
        
        # Переключаемся обратно на PostgreSQL
        settings.DATABASES['default'] = original_db
        apps.clear_cache()
        
        # Создаем группы
        group_map = {}
        for group_id, group_name in groups_data:
            group, created = Group.objects.get_or_create(
                id=group_id,
                defaults={'name': group_name}
            )
            group_map[group_id] = group
            if created:
                print(f"Создана группа: {group_name}")
        
        # Создаем студентов
        student_map = {}
        for student_id, full_name, group_id in students_data:
            if group_id in group_map:
                student, created = Student.objects.get_or_create(
                    id=student_id,
                    defaults={
                        'full_name': full_name,
                        'group': group_map[group_id]
                    }
                )
                student_map[student_id] = student
                if created:
                    print(f"Создан студент: {full_name}")
        
        # Создаем проекты
        for (project_id, student_id, archive, uploaded_at, status, 
             backend_port, frontend_port, backend_url, frontend_url,
             container_id_backend, container_id_frontend) in projects_data:
            
            if student_id in student_map:
                project, created = ProjectUpload.objects.get_or_create(
                    id=project_id,
                    defaults={
                        'student': student_map[student_id],
                        'archive': archive,
                        'uploaded_at': uploaded_at,
                        'status': status or 'uploaded',
                        'backend_port': backend_port,
                        'frontend_port': frontend_port,
                        'backend_url': backend_url,
                        'frontend_url': frontend_url,
                        'container_id_backend': container_id_backend,
                        'container_id_frontend': container_id_frontend,
                    }
                )
                if created:
                    print(f"Создан проект ID: {project_id}")
        
        print("Миграция данных завершена успешно!")
        return True
        
    except Exception as e:
        print(f"Ошибка при миграции данных: {e}")
        return False

if __name__ == "__main__":
    if migrate_data():
        print("Миграция завершена успешно!")
    else:
        print("Ошибка при миграции данных.")
        sys.exit(1) 
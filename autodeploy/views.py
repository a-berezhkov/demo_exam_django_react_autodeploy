from django.shortcuts import render, redirect
from .forms import ProjectUploadForm
from .models import Student, ProjectUpload, Group
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import mimetypes

import os
import tempfile
import zipfile
import tarfile
import shutil
import subprocess
import socket
import yaml
import re
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from pathlib import Path

PROJECTS_ROOT = 'student_projects'
BACKEND_PORT_START = 8100
FRONTEND_PORT_START = 3100

BACKEND_DOCKERFILE = '''\
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
'''

FRONTEND_DOCKERFILE = '''\
FROM node:20
WORKDIR /app
ENV NODE_ENV=development
ENV PATH /app/node_modules/.bin:$PATH
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
'''

REQUIREMENTS_TXT = '''\
django
djangorestframework
django-cors-headers
Pillow
'''

def get_and_assign_port(project, port_type, start_port):
    from .models import ProjectUpload
    for _ in range(5):  # 5 попыток
        try:
            with transaction.atomic():
                # Блокируем строки с портами
                if port_type == 'backend':
                    used_ports = set(ProjectUpload.objects.select_for_update().exclude(backend_port=None).values_list('backend_port', flat=True))
                else:
                    used_ports = set(ProjectUpload.objects.select_for_update().exclude(frontend_port=None).values_list('frontend_port', flat=True))
                max_port = max(used_ports) if used_ports else start_port - 1
                port = max_port + 1
                # Проверяем реальную доступность порта на хосте
                import socket
                while port < 65535:
                    if port not in used_ports:
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.bind(('localhost', port))
                                s.close()
                                # Назначаем порт и сохраняем проект
                                if port_type == 'backend':
                                    project.backend_port = port
                                else:
                                    project.frontend_port = port
                                project.save()
                                return port
                        except OSError:
                            pass
                    port += 1
                raise RuntimeError('Нет свободных портов')
        except IntegrityError:
            continue
    raise RuntimeError('Не удалось назначить уникальный порт')


def find_project_dirs(root_path):
    # Сначала ищем в корне
    dirs = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]
    if 'frontend' in dirs and 'backend' in dirs:
        return True, dirs
    # Если в корне только одна папка, ищем внутри неё
    if len(dirs) == 1:
        sub_path = os.path.join(root_path, dirs[0])
        sub_dirs = [d for d in os.listdir(sub_path) if os.path.isdir(os.path.join(sub_path, d))]
        if 'frontend' in sub_dirs and 'backend' in sub_dirs:
            return True, sub_dirs
        return False, sub_dirs
    return False, dirs


def get_next_free_port(start_port, port_type):
    """Назначает следующий за максимальным портом, который уже используется в БД, и проверяет его реальную доступность на хосте."""
    from .models import ProjectUpload
    used_ports = set()
    if port_type == 'backend':
        used_ports = set(ProjectUpload.objects.exclude(backend_port=None).values_list('backend_port', flat=True))
    elif port_type == 'frontend':
        used_ports = set(ProjectUpload.objects.exclude(frontend_port=None).values_list('frontend_port', flat=True))
    max_port = max(used_ports) if used_ports else start_port - 1
    port = max_port + 1
    while port < 65535:
        if port not in used_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    s.close()
                    return port
            except OSError:
                pass
        port += 1
    raise RuntimeError('Нет свободных портов')


def generate_docker_compose(project_dir, backend_port, frontend_port):
    compose = {
        'version': '3',
        'services': {
            'backend': {
                'build': './backend',
                'working_dir': '/app',
                'command': 'python manage.py runserver 0.0.0.0:8000',
                'ports': [f'{backend_port}:8000'],
                'networks': {
                    'projects_network': {
                        'aliases': ['localhost']
                    }
                },
            },
            'frontend': {
                'build': './frontend',
                'working_dir': '/app',
                'command': 'npx vite --host',
                'ports': [f'{frontend_port}:5173'],
                'environment': [f'VITE_URL=http://217.196.101.222:{backend_port}/api/'],
                 'ulimits': {
                    'nofile': {
                        'soft': 65536,
                        'hard': 65536
                    }
                },
                'networks': {
                    'projects_network': {}
                },
            },
        },
        'networks': {
            'projects_network': {
                'external': True  # Используем внешнюю сеть
            }
        }
    }
    with open(os.path.join(project_dir, 'docker-compose.yml'), 'w') as f:
        yaml.dump(compose, f, default_flow_style=False, allow_unicode=True)


def find_settings_file(backend_dir):
    """
    Рекурсивно ищет файл settings.py в директории backend.
    Возвращает полный путь к файлу или None, если файл не найден.
    """
    for root, dirs, files in os.walk(backend_dir):
        if 'settings.py' in files:
            return os.path.join(root, 'settings.py')
    
    return None


def setup_and_run_containers(project: ProjectUpload, tmpdir: str):
    os.makedirs(PROJECTS_ROOT, exist_ok=True)
    project_dir = os.path.join(PROJECTS_ROOT, str(project.id))
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    os.makedirs(project_dir)
    # Копируем папки
    dirs = [d for d in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, d))]
    if 'frontend' in dirs and 'backend' in dirs:
        shutil.copytree(os.path.join(tmpdir, 'frontend'), os.path.join(project_dir, 'frontend'))
        shutil.copytree(os.path.join(tmpdir, 'backend'), os.path.join(project_dir, 'backend'))
    elif len(dirs) == 1:
        sub_path = os.path.join(tmpdir, dirs[0])
        shutil.copytree(os.path.join(sub_path, 'frontend'), os.path.join(project_dir, 'frontend'))
        shutil.copytree(os.path.join(sub_path, 'backend'), os.path.join(project_dir, 'backend'))
    else:
        raise Exception('Не найдены папки frontend и backend для копирования')
    # Удаляем requirements.txt, если он есть, и создаём свой
    requirements_path = os.path.join(project_dir, 'backend', 'requirements.txt')
    if os.path.exists(requirements_path):
        os.remove(requirements_path)
    with open(requirements_path, 'w') as f:
        f.write(REQUIREMENTS_TXT)
    # Генерируем Dockerfile, если его нет
    backend_dockerfile = os.path.join(project_dir, 'backend', 'Dockerfile')
    if not os.path.exists(backend_dockerfile):
        with open(backend_dockerfile, 'w') as f:
            f.write(BACKEND_DOCKERFILE)
    frontend_dockerfile = os.path.join(project_dir, 'frontend', 'Dockerfile')
    if not os.path.exists(frontend_dockerfile):
        with open(frontend_dockerfile, 'w') as f:
            f.write(FRONTEND_DOCKERFILE)
    # Удаляем package-lock.json и node_modules в frontend всегда
    frontend_dir = os.path.join(project_dir, 'frontend')
    lock_path = os.path.join(frontend_dir, 'package-lock.json')
    node_modules_path = os.path.join(frontend_dir, 'node_modules')
    if os.path.exists(lock_path):
        os.remove(lock_path)
    if os.path.exists(node_modules_path):
        shutil.rmtree(node_modules_path)
    # Переименовываем vite.config.js в vite.config.mjs, если есть
    vite_config_js = os.path.join(frontend_dir, 'vite.config.js')
    vite_config_mjs = os.path.join(frontend_dir, 'vite.config.mjs')
    if os.path.exists(vite_config_js):
        os.rename(vite_config_js, vite_config_mjs)
    # Выделяем порты с учетом БД и реальной занятости, начиная с максимального
    backend_port = get_and_assign_port(project, 'backend', BACKEND_PORT_START)
    frontend_port = get_and_assign_port(project, 'frontend', FRONTEND_PORT_START)
    # Получаем внешний IP из ALLOWED_HOSTS
    external_ip = next((host for host in settings.ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']), 'localhost')
    # Ищем файл settings.py в backend
    backend_dir = os.path.join(project_dir, 'backend')
    backend_settings_path = find_settings_file(backend_dir)
    
    if backend_settings_path and os.path.exists(backend_settings_path):
        with open(backend_settings_path, 'r') as f:
            content = f.read()
        # Заменяем ALLOWED_HOSTS на нужный список
        new_content, n = re.subn(
            r'ALLOWED_HOSTS\s*=\s*\[.*?\]',
            f"ALLOWED_HOSTS = ['{external_ip}', 'localhost', '127.0.0.1']",
            content,
            flags=re.DOTALL
        )
        if n == 0:
            # Если ALLOWED_HOSTS не найден, добавим в конец файла
            new_content = content + f"\nALLOWED_HOSTS = ['{external_ip}', 'localhost', '127.0.0.1']\n"
        with open(backend_settings_path, 'w') as f:
            f.write(new_content)
    # Создаём/обновляем .env во frontend с VITE_URL
    env_path = os.path.join(frontend_dir, '.env')
    vite_url_line = f'VITE_URL=http://217.196.101.222:{backend_port}/api/\n'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
        with open(env_path, 'w') as f:
            found = False
            for line in lines:
                if line.startswith('VITE_URL='):
                    f.write(vite_url_line)
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(vite_url_line)
    else:
        with open(env_path, 'w') as f:
            f.write(vite_url_line)
    # Создаем общую сеть, если её нет
    try:
        subprocess.run(['docker', 'network', 'create', '--subnet=172.20.0.0/16', '--gateway=172.20.0.1', 'projects_network'], 
                      capture_output=True, text=True)
    except:
        pass  # Сеть уже существует
    # Генерируем docker-compose.yml
    generate_docker_compose(project_dir, backend_port, frontend_port)
    # Запускаем контейнеры
    result = subprocess.run(['docker-compose', 'up', '-d'], cwd=project_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f'Ошибка запуска контейнеров: {result.stderr}')
    # Получаем id контейнеров
    ps = subprocess.run(['docker-compose', 'ps', '-q', 'backend'], cwd=project_dir, capture_output=True, text=True)
    backend_id = ps.stdout.strip()
    ps = subprocess.run(['docker-compose', 'ps', '-q', 'frontend'], cwd=project_dir, capture_output=True, text=True)
    frontend_id = ps.stdout.strip()
    # Сохраняем в БД
    project.backend_port = backend_port
    project.frontend_port = frontend_port
    project.backend_url = f'http://{external_ip}:{backend_port}/api/'
    project.frontend_url = f'http://{external_ip}:{frontend_port}/'
    project.container_id_backend = backend_id
    project.container_id_frontend = frontend_id
    project.status = 'running'
    project.save()


def access_denied(request, exception):
    """Обработчик ошибки доступа - перенаправляет на страницу загрузки"""
    messages.warning(request, 'Доступ только для администраторов. Для управления проектами войдите в админку.')
    return redirect('upload_project')


def redirect_to_upload(request):
    """Перенаправляет неавторизованных пользователей на страницу загрузки"""
    return redirect('upload_project')


def upload_project(request):
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            group = form.cleaned_data['group']
            archive = form.cleaned_data['archive']
            try:
                with transaction.atomic():
                    student, _ = Student.objects.get_or_create(full_name=full_name, group=group)
                    project = ProjectUpload.objects.create(student=student, archive=archive)
                    
                    # Проверка архива
                    with tempfile.TemporaryDirectory() as tmpdir:
                        archive_path = project.archive.path
                        if archive_path.endswith('.zip'):
                            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                                zip_ref.extractall(tmpdir)
                        elif archive_path.endswith('.tar') or archive_path.endswith('.tar.gz'):
                            with tarfile.open(archive_path, 'r:*') as tar_ref:
                                tar_ref.extractall(tmpdir)
                        else:
                            project.status = 'error'
                            project.save()
                            messages.error(request, 'Неподдерживаемый формат архива.')
                            return redirect('upload_project')
                        
                        # Улучшенная проверка наличия папок
                        found, found_dirs = find_project_dirs(tmpdir)
                        if found:
                            try:
                                setup_and_run_containers(project, tmpdir)
                                # Показываем ссылки после успешного запуска
                                return render(request, 'autodeploy/upload.html', {
                                    'form': ProjectUploadForm(),
                                    'messages': messages.get_messages(request),
                                    'frontend_url': project.frontend_url,
                                    'backend_url': project.backend_url,
                                    'project': project,
                                })
                            except Exception as e:
                                project.status = 'error'
                                project.save()
                                messages.error(request, f'Ошибка запуска контейнеров: {e}')
                                return redirect('upload_project')
                        else:
                            project.status = 'error'
                            project.save()
                            messages.error(request, f'В архиве должны быть папки frontend и backend. Найдено: {found_dirs}')
                            return redirect('upload_project')
                    
                    # Если дошли до сюда, значит проект успешно загружен
                    messages.success(request, 'Архив успешно загружен!')
                    return redirect('upload_project')
                    
            except Exception as e:
                messages.error(request, f'Ошибка загрузки: {e}')
    else:
        form = ProjectUploadForm()
    return render(request, 'autodeploy/upload.html', {'form': form, 'messages': messages.get_messages(request)})


@staff_member_required
def all_projects(request):
    fio_query = request.GET.get('fio', '').strip()
    group_id = request.GET.get('group', '')
    projects = ProjectUpload.objects.select_related('student', 'student__group')
    if fio_query:
        projects = projects.filter(student__full_name__icontains=fio_query)
    if group_id:
        projects = projects.filter(student__group__id=group_id)
    projects = projects.order_by('-uploaded_at')
    
    # Статистика
    total_projects = projects.count()
    running_projects = projects.filter(status='running').count()
    stopped_projects = projects.filter(status='stopped').count()
    error_projects = projects.filter(status='error').count()
    
    groups = Group.objects.all()
    return render(request, 'autodeploy/all_projects.html', {
        'projects': projects,
        'groups': groups,
        'fio_query': fio_query,
        'group_id': group_id,
        'total_projects': total_projects,
        'running_projects': running_projects,
        'stopped_projects': stopped_projects,
        'error_projects': error_projects,
    })


@staff_member_required
def download_archive(request, project_id):
    try:
        project = ProjectUpload.objects.get(id=project_id)
        archive_path = project.archive.path
        archive_name = project.archive.name.split('/')[-1]
        with open(archive_path, 'rb') as f:
            mime_type, _ = mimetypes.guess_type(archive_path)
            response = HttpResponse(f.read(), content_type=mime_type or 'application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{archive_name}"'
            return response
    except ProjectUpload.DoesNotExist:
        raise Http404('Архив не найден')
    except Exception:
        raise Http404('Ошибка при скачивании архива')


@csrf_exempt
@staff_member_required
def manage_container(request, project_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Список контейнеров, которые нужно исключить из операций
        excluded_containers = [
            'my_postgres',  # PostgreSQL контейнер
            'postgres',     # Любые postgres контейнеры
            'mysql',        # MySQL контейнеры
            'redis',        # Redis контейнеры
            'nginx',        # Основной nginx
            'adminer',      # Adminer
            'phpmyadmin',   # phpMyAdmin
        ]
        
        try:
            project = ProjectUpload.objects.get(id=project_id)
            project_dir = Path('student_projects') / str(project.id)
            
            # Проверяем, что контейнеры проекта не в списке исключений
            should_manage = True
            if project_dir.exists():
                compose_path = project_dir / 'docker-compose.yml'
                if compose_path.exists():
                    with open(compose_path, 'r') as f:
                        compose_data = yaml.safe_load(f)
                    
                    services = compose_data.get('services', {})
                    for service_name in services:
                        if any(excluded in service_name.lower() for excluded in excluded_containers):
                            should_manage = False
                            messages.warning(request, f'Проект {project_id} содержит системные контейнеры и не может быть изменен.')
                            break
            
            if should_manage:
                if action == 'start':
                    # Запуск контейнеров
                    result = subprocess.run(['docker-compose', 'up', '-d'], cwd=project_dir, capture_output=True, text=True)
                    if result.returncode == 0:
                        project.status = 'running'
                        # Обновляем ссылки после успешного запуска
                        try:
                            # Читаем docker-compose.yml для получения портов
                            compose_path = project_dir / 'docker-compose.yml'
                            if compose_path.exists():
                                with open(compose_path, 'r') as f:
                                    compose_data = yaml.safe_load(f)
                                
                                # Извлекаем порты из docker-compose.yml
                                backend_ports = compose_data.get('services', {}).get('backend', {}).get('ports', [])
                                frontend_ports = compose_data.get('services', {}).get('frontend', {}).get('ports', [])
                                
                                if backend_ports and frontend_ports:
                                    # Парсим порты (формат "8101:8000")
                                    backend_port = int(backend_ports[0].split(':')[0])
                                    frontend_port = int(frontend_ports[0].split(':')[0])
                                    
                                    # Получаем внешний IP
                                    external_ip = next((host for host in settings.ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']), 'localhost')
                                    
                                    # Обновляем поля проекта
                                    project.backend_port = backend_port
                                    project.frontend_port = frontend_port
                                    project.backend_url = f'http://{external_ip}:{backend_port}/api/'
                                    project.frontend_url = f'http://{external_ip}:{frontend_port}/'
                        except Exception as e:
                            # Если не удалось получить порты, оставляем как есть
                            pass
                    else:
                        project.status = 'error'
                    project.save()
                elif action == 'stop':
                    # Остановка контейнеров
                    result = subprocess.run(['docker-compose', 'down'], cwd=project_dir, capture_output=True, text=True)
                    if result.returncode == 0:
                        project.status = 'stopped'
                    else:
                        project.status = 'error'
                    project.save()
                elif action == 'delete':
                    # Полное удаление проекта
                    try:
                        # 1. Остановка контейнеров
                        result = subprocess.run(['docker-compose', 'down'], cwd=project_dir, capture_output=True, text=True)
                        
                        # 2. Удаление образов (если контейнеры успешно остановлены)
                        if result.returncode == 0:
                            # Получаем имена образов из docker-compose.yml
                            compose_path = project_dir / 'docker-compose.yml'
                            if compose_path.exists():
                                with open(compose_path, 'r') as f:
                                    compose_data = yaml.safe_load(f)
                                
                                # Удаляем образы для backend и frontend
                                services = compose_data.get('services', {})
                                for service_name in ['backend', 'frontend']:
                                    if service_name in services:
                                        # Получаем имя образа или генерируем его
                                        image_name = services[service_name].get('image')
                                        if not image_name:
                                            # Если image не указан, используем имя проекта
                                            image_name = f"{project_dir.name}_{service_name}"
                                        
                                        # Удаляем образ
                                        subprocess.run(['docker', 'rmi', '-f', image_name], 
                                                     capture_output=True, text=True)
                        
                        # 3. Удаление файлов проекта
                        if project_dir.exists():
                            shutil.rmtree(project_dir)
                        
                        # 4. Удаление из базы данных
                        project.delete()
                        
                    except Exception as e:
                        # Если что-то пошло не так, все равно удаляем из БД
                        try:
                            project.delete()
                        except:
                            pass
        except ProjectUpload.DoesNotExist:
            pass
    return redirect(reverse('all_projects'))


@csrf_exempt
@staff_member_required
def manage_all_containers(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        projects = ProjectUpload.objects.all()
        
        # Список контейнеров, которые нужно исключить из операций
        excluded_containers = [
            'my_postgres',  # PostgreSQL контейнер
            'postgres',     # Любые postgres контейнеры
            'mysql',        # MySQL контейнеры
            'redis',        # Redis контейнеры
            'nginx',        # Основной nginx
            'adminer',      # Adminer
            'phpmyadmin',   # phpMyAdmin
        ]
        
        if action == 'stop_all':
            # Остановка всех запущенных контейнеров
            stopped_count = 0
            for project in projects:
                if project.status == 'running':
                    try:
                        project_dir = Path('student_projects') / str(project.id)
                        if project_dir.exists():
                            # Проверяем, что контейнеры проекта не в списке исключений
                            compose_path = project_dir / 'docker-compose.yml'
                            if compose_path.exists():
                                with open(compose_path, 'r') as f:
                                    compose_data = yaml.safe_load(f)
                                
                                # Проверяем имена сервисов
                                services = compose_data.get('services', {})
                                should_stop = True
                                
                                for service_name in services:
                                    # Проверяем, не является ли сервис исключенным
                                    if any(excluded in service_name.lower() for excluded in excluded_containers):
                                        should_stop = False
                                        break
                                
                                if should_stop:
                                    result = subprocess.run(['docker-compose', 'down'], 
                                                          cwd=project_dir, capture_output=True, text=True)
                                    if result.returncode == 0:
                                        project.status = 'stopped'
                                        project.save()
                                        stopped_count += 1
                                    else:
                                        print(f"Ошибка остановки проекта {project.id}: {result.stderr}")
                                else:
                                    print(f"Пропущен проект {project.id} - содержит исключенные контейнеры")
                    except Exception as e:
                        print(f"Ошибка остановки проекта {project.id}: {e}")
            
            messages.success(request, f'Остановлено контейнеров: {stopped_count}')
            
        elif action == 'start_all':
            # Запуск всех остановленных контейнеров
            started_count = 0
            for project in projects:
                if project.status in ['stopped', 'uploaded']:
                    try:
                        project_dir = Path('student_projects') / str(project.id)
                        if project_dir.exists():
                            result = subprocess.run(['docker-compose', 'up', '-d'], 
                                                  cwd=project_dir, capture_output=True, text=True)
                            if result.returncode == 0:
                                project.status = 'running'
                                project.save()
                                started_count += 1
                    except Exception as e:
                        print(f"Ошибка запуска проекта {project.id}: {e}")
            
            messages.success(request, f'Запущено контейнеров: {started_count}')
            
        elif action == 'delete_all':
            # Удаление всех контейнеров и проектов
            deleted_count = 0
            for project in projects:
                try:
                    project_dir = Path('student_projects') / str(project.id)
                    
                    # Проверяем, что контейнеры проекта не в списке исключений
                    should_delete = True
                    if project_dir.exists():
                        compose_path = project_dir / 'docker-compose.yml'
                        if compose_path.exists():
                            with open(compose_path, 'r') as f:
                                compose_data = yaml.safe_load(f)
                            
                            services = compose_data.get('services', {})
                            for service_name in services:
                                if any(excluded in service_name.lower() for excluded in excluded_containers):
                                    should_delete = False
                                    print(f"Пропущен проект {project.id} - содержит исключенные контейнеры")
                                    break
                    
                    if should_delete:
                        # Остановка контейнеров
                        if project_dir.exists():
                            subprocess.run(['docker-compose', 'down'], 
                                         cwd=project_dir, capture_output=True, text=True)
                            
                            # Удаление образов
                            try:
                                compose_path = project_dir / 'docker-compose.yml'
                                if compose_path.exists():
                                    with open(compose_path, 'r') as f:
                                        compose_data = yaml.safe_load(f)
                                    
                                    services = compose_data.get('services', {})
                                    for service_name in ['backend', 'frontend']:
                                        if service_name in services:
                                            image_name = services[service_name].get('image')
                                            if not image_name:
                                                image_name = f"{project_dir.name}_{service_name}"
                                            
                                            subprocess.run(['docker', 'rmi', '-f', image_name], 
                                                         capture_output=True, text=True)
                            except Exception as e:
                                print(f"Ошибка удаления образов проекта {project.id}: {e}")
                            
                            # Удаление файлов проекта
                            shutil.rmtree(project_dir)
                        
                        # Удаление из базы данных
                        project.delete()
                        deleted_count += 1
                    
                except Exception as e:
                    print(f"Ошибка удаления проекта {project.id}: {e}")
                    # Если не удалось удалить файлы, все равно удаляем из БД
                    try:
                        project.delete()
                        deleted_count += 1
                    except:
                        pass
            
            # Очистка неиспользуемых Docker ресурсов (кроме исключенных)
            try:
                # Получаем список всех контейнеров
                result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    containers = result.stdout.strip().split('\n')
                    
                    # Удаляем только контейнеры, не входящие в список исключений
                    for container in containers:
                        if container and not any(excluded in container.lower() for excluded in excluded_containers):
                            subprocess.run(['docker', 'rm', '-f', container], capture_output=True, text=True)
                
                # Очищаем неиспользуемые образы и сети
                subprocess.run(['docker', 'system', 'prune', '-f'], capture_output=True, text=True)
                subprocess.run(['docker', 'network', 'prune', '-f'], capture_output=True, text=True)
            except Exception as e:
                print(f"Ошибка очистки Docker ресурсов: {e}")
            
            messages.success(request, f'Удалено проектов: {deleted_count}. Docker ресурсы очищены (исключая системные контейнеры).')
        
        elif action == 'cleanup_docker':
            # Очистка неиспользуемых Docker ресурсов (кроме исключенных)
            try:
                # Получаем список всех контейнеров
                result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    containers = result.stdout.strip().split('\n')
                    
                    # Удаляем только контейнеры, не входящие в список исключений
                    for container in containers:
                        if container and not any(excluded in container.lower() for excluded in excluded_containers):
                            subprocess.run(['docker', 'rm', '-f', container], capture_output=True, text=True)
                
                # Очищаем неиспользуемые образы и сети
                subprocess.run(['docker', 'system', 'prune', '-f'], capture_output=True, text=True)
                subprocess.run(['docker', 'network', 'prune', '-f'], capture_output=True, text=True)
                messages.success(request, 'Docker ресурсы очищены успешно (исключая системные контейнеры).')
            except Exception as e:
                messages.error(request, f'Ошибка очистки Docker ресурсов: {e}')
    
    return redirect(reverse('all_projects'))

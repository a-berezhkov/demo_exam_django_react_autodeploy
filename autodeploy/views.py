from django.shortcuts import render, redirect
from .forms import ProjectUploadForm
from .models import Student, ProjectUpload, Group
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.conf import settings
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
'''


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


def get_free_port(start_port):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
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
                    'default': {
                        'aliases': ['localhost']
                    }
                },
            },
            'frontend': {
                'build': './frontend',
                'working_dir': '/app',
                'command': 'npx vite --host',
                'ports': [f'{frontend_port}:5173'],
                'environment': [f'VITE_URL=http://localhost:{backend_port}/api/'],
            },
        },
        'networks': {
            'default': {
                'driver': 'bridge'
            }
        }
    }
    with open(os.path.join(project_dir, 'docker-compose.yml'), 'w') as f:
        yaml.dump(compose, f, default_flow_style=False, allow_unicode=True)


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
    # Выделяем порты
    backend_port = get_free_port(BACKEND_PORT_START)
    frontend_port = get_free_port(FRONTEND_PORT_START)
    # Получаем внешний IP из ALLOWED_HOSTS
    external_ip = next((host for host in settings.ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']), 'localhost')
    # Добавляем внешний IP в ALLOWED_HOSTS backend settings.py
    backend_settings_path = os.path.join(project_dir, 'backend', 'config', 'settings.py')
    if not os.path.exists(backend_settings_path):
        backend_settings_path = os.path.join(project_dir, 'backend', 'settings.py')
    if os.path.exists(backend_settings_path):
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
    vite_url_line = f'VITE_URL=http://{external_ip}:{backend_port}/api/\n'
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
                        else:
                            project.status = 'error'
                            messages.error(request, f'В архиве должны быть папки frontend и backend. Найдено: {found_dirs}')
                        project.save()
                    if project.status == 'uploaded':
                        messages.success(request, 'Архив успешно загружен!')
                        return redirect('upload_project')
            except Exception as e:
                messages.error(request, f'Ошибка загрузки: {e}')
    else:
        form = ProjectUploadForm()
    return render(request, 'autodeploy/upload.html', {'form': form, 'messages': messages.get_messages(request)})


def all_projects(request):
    fio_query = request.GET.get('fio', '').strip()
    group_id = request.GET.get('group', '')
    projects = ProjectUpload.objects.select_related('student', 'student__group')
    if fio_query:
        projects = projects.filter(student__full_name__icontains=fio_query)
    if group_id:
        projects = projects.filter(student__group__id=group_id)
    projects = projects.order_by('-uploaded_at')
    groups = Group.objects.all()
    return render(request, 'autodeploy/all_projects.html', {
        'projects': projects,
        'groups': groups,
        'fio_query': fio_query,
        'group_id': group_id,
    })


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
def manage_container(request, project_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            project = ProjectUpload.objects.get(id=project_id)
            project_dir = Path('student_projects') / str(project.id)
            if action == 'start':
                # Запуск контейнеров
                result = subprocess.run(['docker-compose', 'up', '-d'], cwd=project_dir, capture_output=True, text=True)
                if result.returncode == 0:
                    project.status = 'running'
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
                # Остановка и удаление контейнеров + очистка полей
                subprocess.run(['docker-compose', 'down', '--volumes'], cwd=project_dir)
                project.status = 'uploaded'
                project.container_id_backend = None
                project.container_id_frontend = None
                project.backend_port = None
                project.frontend_port = None
                project.backend_url = None
                project.frontend_url = None
                project.save()
        except ProjectUpload.DoesNotExist:
            pass
    return redirect(reverse('all_projects'))

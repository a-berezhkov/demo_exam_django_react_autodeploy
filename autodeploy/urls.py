from django.urls import path
from .views import upload_project, all_projects, download_archive, manage_container, redirect_to_upload

urlpatterns = [
    path('', redirect_to_upload, name='home'),
    path('upload/', upload_project, name='upload_project'),
    path('projects/', all_projects, name='all_projects'),
    path('download-archive/<int:project_id>/', download_archive, name='download_archive'),
    path('manage-container/<int:project_id>/', manage_container, name='manage_container'),
] 
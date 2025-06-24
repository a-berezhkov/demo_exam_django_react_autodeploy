from django.urls import path
from .views import upload_project, all_projects

urlpatterns = [
    path('upload/', upload_project, name='upload_project'),
    path('projects/', all_projects, name='all_projects'),
] 
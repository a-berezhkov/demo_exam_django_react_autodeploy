from django.db import models

# Create your models here.

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    full_name = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.full_name

class ProjectUpload(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    archive = models.FileField(upload_to='archives/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    backend_port = models.IntegerField(null=True, blank=True)
    frontend_port = models.IntegerField(null=True, blank=True)
    backend_url = models.URLField(null=True, blank=True)
    frontend_url = models.URLField(null=True, blank=True)
    container_id_backend = models.CharField(max_length=128, null=True, blank=True)
    container_id_frontend = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=32, default='uploaded')  # uploaded, running, stopped, error

    def __str__(self):
        return f"{self.student.full_name} ({self.student.group.name})"

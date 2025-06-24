from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    name = models.CharField(max_length=123)
    role = models.CharField(max_length=123)
    email = models.EmailField(unique=True)

class Category(models.Model):
    name = models.CharField(max_length=123)

class Book(models.Model):
    title = models.CharField(max_length=123)
    author = models.CharField(max_length=123)
    cover = models.URLField(max_length=1233)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class BookDownload(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    title = models.CharField(max_length=123)
    author = models.CharField(max_length=123)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    download_date = models.DateField(auto_now_add=True)
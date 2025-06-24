from .views import LoginUserView, RegisterUserView, BookViewset, CategoryViewset, UserProfileView, DownloadBookView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(prefix='books', viewset=BookViewset)
router.register(prefix='admin/categories', viewset=CategoryViewset)


urlpatterns = [
    path('auth/login', LoginUserView.as_view()),
    path('auth/register', RegisterUserView.as_view()),
    path('profile/', UserProfileView.as_view()),
    path("", include(router.urls)),
    path('downloads', DownloadBookView.as_view()),
    path('books/<int:pk>/download', DownloadBookView.as_view())
]
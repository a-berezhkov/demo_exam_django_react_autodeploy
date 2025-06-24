from django.http import Http404
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from .serializers import RegisterSerializer, LoginSer, BookDownloadSer, BookSerializer, BookCreateSerializer, \
    UserProfileSer, CategorySerializer
from rest_framework.authtoken.models import Token
from .permissions import IsTeacherOrAdminOrReadOnly
from rest_framework.authentication import authenticate
from django.shortcuts import get_object_or_404
from .models import CustomUser, Book, Category, BookDownload


class CustomResponse(Response):
    def __init__(self, data=None, message='success', status=200):
        d = {
            "message": message,
            'data': data
        }
        super().__init__(d, status)


class RegisterUserView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        token = Token.objects.create(user=user)

        return CustomResponse(
            data={
                'token': token.key,
                'user': RegisterSerializer(instance=user).data
            },
            status=201
        )


class LoginUserView(APIView):
    serializer_class = LoginSer

    def post(self, request):
        s = LoginSer(data=request.data)
        s.is_valid(raise_exception=True)

        user = authenticate(username=request.data['email'], password=request.data['password'])
        if not user:
            raise AuthenticationFailed()

        token, _ = Token.objects.get_or_create(user=user)

        return CustomResponse(
            data={
                'token': token.key,
                'user': RegisterSerializer(instance=user).data
            }
        )


class BookViewset(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsTeacherOrAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if len(queryset) < 1:
            raise Http404('No books found')

        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = BookCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        a = serializer.save()
        return CustomResponse(data=BookSerializer(instance=a).data, status=201)

    def perform_update(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = BookCreateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        book = self.perform_update(serializer)
        return CustomResponse(data=BookSerializer(instance=book).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return CustomResponse(data=None)

    def perform_destroy(self, instance):
        instance.delete()


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        s = UserProfileSer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.data
        if 'email' in d:
            d['username'] = d['email']
        s2 = UserProfileSer(instance=request.user, data=d, partial=True)
        s2.is_valid(raise_exception=True)
        user = s2.save()

        return CustomResponse(
            data=UserProfileSer(instance=user).data
        )

    def get(self, request):
        s = UserProfileSer(instance=request.user)
        return CustomResponse(data=s.data)


class CategoryViewset(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if len(queryset) < 1:
            raise Http404('No cats found')

        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return CustomResponse(data=serializer.data, status=201)

    def perform_update(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = CategorySerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        book = self.perform_update(serializer)
        return CustomResponse(data=CategorySerializer(instance=book).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return CustomResponse(data=None)

    def perform_destroy(self, instance):
        instance.delete()


class DownloadBookView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        books = BookDownload.objects.filter(user=request.user)
        s = BookDownloadSer(instance=books, many=True)
        return CustomResponse(data=s.data)

    def post(self, request, pk=None):
        book = get_object_or_404(Book, id=pk)

        bd = BookDownload.objects.create(
            book=book,
            user=request.user,
            title=book.title,
            author=book.author
        )
        s = BookDownloadSer(instance=bd)
        return CustomResponse(
            data={
                'book_id': book.id,
                'title': book.title,
                'download_date': s.data['download_date']
            }
        )

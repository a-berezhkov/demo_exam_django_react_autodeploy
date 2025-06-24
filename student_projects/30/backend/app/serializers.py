from .models import CustomUser, Category, Book, BookDownload
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','name', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data, username=validated_data['email'])


class LoginSer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']
        extra_kwargs= {
            'email': {
                'validators': []
            }
        }

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name']

class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'cover', 'category']

class BookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'cover', 'category']

class UserProfileSer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'role']
        extra_kwargs = {
            'email': {
                "validators": []
            }
        }


class BookDownloadSer(serializers.ModelSerializer):
    download_date = serializers.DateField(format="%Y-%d-%m")
    class Meta:
        model = BookDownload
        fields = ['id', 'title', 'author', 'download_date']
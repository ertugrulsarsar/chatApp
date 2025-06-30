from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    """Kullanıcı modeli için serializer."""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'password_confirm', 'is_online', 'last_seen']
        read_only_fields = ['id', 'is_online', 'last_seen']
    
    def validate(self, attrs):
        """Şifre doğrulama."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Şifreler eşleşmiyor.")
        return attrs
    
    def create(self, validated_data):
        """Kullanıcı oluşturma."""
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Özel JWT token serializer."""
    
    def validate(self, attrs):
        """Token doğrulama ve kullanıcı bilgilerini ekleme."""
        data = super().validate(attrs)
        
        # Kullanıcıyı online yap
        self.user.is_online = True
        self.user.save()
        
        # Token'a kullanıcı bilgilerini ekle
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'is_online': self.user.is_online,
        }
        
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    """Kullanıcı profil serializer'ı."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'is_online', 'last_seen', 'is_2fa_enabled']
        read_only_fields = ['id', 'is_online', 'last_seen']

class ChangePasswordSerializer(serializers.Serializer):
    """Şifre değiştirme serializer'ı."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Şifre doğrulama."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Yeni şifreler eşleşmiyor.")
        return attrs
    
    def validate_old_password(self, value):
        """Eski şifre kontrolü."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski şifre yanlış.")
        return value 
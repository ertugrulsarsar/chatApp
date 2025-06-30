from rest_framework import serializers
from .models import ChatRoom, Message
from users.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı bilgileri için serializer."""
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']

class ChatRoomSerializer(serializers.ModelSerializer):
    """Chat odaları için serializer."""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    members = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'description', 'members', 'room_type', 'password', 'created_at']
        read_only_fields = ['members', 'created_at']

    def create(self, validated_data):
        # Şifre girilmişse hash'le
        if 'password' in validated_data and validated_data['password']:
            from django.contrib.auth.hashers import make_password
            validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class MessageSerializer(serializers.ModelSerializer):
    """Mesajlar için serializer."""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 
            'room', 
            'sender', 
            'sender_username', 
            'content', 
            'created_at', 
            'is_deleted'
        ]
        read_only_fields = ['sender', 'created_at', 'is_deleted'] 
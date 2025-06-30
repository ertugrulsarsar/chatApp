from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF Router
router = DefaultRouter()
router.register(r'rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = 'chat'

urlpatterns = [
    # Template Views
    path('', views.chat_room_list, name='chat_room_list'),
    path('create/', views.create_chat_room, name='create_chat_room'),
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('join/<int:room_id>/', views.join_room, name='join_room'),
    path('manage/<int:room_id>/', views.room_management, name='room_management'),
    
    # API Views
    path('api/', include(router.urls)),
    path('api/rooms/', views.ChatRoomListCreateView.as_view(), name='api_rooms'),
    path('api/rooms/<int:pk>/', views.ChatRoomDetailView.as_view(), name='api_room_detail'),
    path('api/rooms/<int:room_id>/messages/', views.MessageListView.as_view(), name='api_messages'),
    path('api/messages/<int:pk>/edit/', views.MessageEditView.as_view(), name='api_message_edit'),
    path('api/messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='api_message_delete'),
    path('upload_file/', views.upload_file, name='upload_file'),
    
    # Room Management API
    path('room/<int:room_id>/members/', views.room_members, name='room_members'),
    path('room/<int:room_id>/statistics/', views.room_statistics, name='room_statistics'),
    path('room/<int:room_id>/recent-messages/', views.room_recent_messages, name='room_recent_messages'),
] 
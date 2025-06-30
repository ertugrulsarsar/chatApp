from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .forms import ChatRoomForm
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import uuid
from django.contrib import messages

@login_required
def chat_room_list(request):
    """Sohbet odalarını listeler."""
    rooms = ChatRoom.objects.all()
    return render(request, 'chat/chat_room_list.html', {
        'rooms': rooms,
        'create_room_url': 'chat:create_chat_room' # URL'yi contexte ekliyoruz
        })

@login_required
def create_chat_room(request):
    """Yeni sohbet odası oluşturur."""
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            chat_room = form.save(commit=False)
            chat_room.created_by = request.user
            # Şifre alanı boş değilse hash'le
            password = form.cleaned_data.get('password')
            if password:
                chat_room.set_password(password)
            chat_room.save()
            # Many-to-many ilişkisini kaydetmek için
            form.save_m2m()
            # Odayı oluşturan kişiyi katılımcı olarak ekle
            chat_room.members.add(request.user)
            return redirect('chat:chat_room_list')
    else:
        form = ChatRoomForm()
    return render(request, 'chat/create_room.html', {'form': form})

@login_required
def chat_room(request, room_id):
    """Belirli bir sohbet odasını ve mesajlarını gösterir."""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Kullanıcı oda üyesi mi kontrol et
    if request.user not in room.members.all():
        # Üye değilse katılma sayfasına yönlendir
        return redirect('chat:join_room', room_id=room_id)

    messages = Message.objects.filter(room=room, is_deleted=False).order_by('created_at')
    members = room.members.all().select_related()
    
    return render(request, 'chat/chat_room.html', {
        'room': room,
        'messages': messages,
        'members': members,
        'can_manage': room.can_manage(request.user),
    })

@login_required
def join_room(request, room_id):
    """Odaya katılma işlemi. Herkese açık odalarda otomatik katılma, özel odalarda şifre kontrolü."""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Kullanıcı zaten üye mi kontrol et
    if request.user in room.members.all():
        return redirect('chat:chat_room', room_id=room_id)
    
    if request.method == 'POST':
        if room.room_type == 'private':
            # Özel oda - şifre kontrolü
            password = request.POST.get('password')
            if not password:
                return render(request, 'chat/join_room.html', {
                    'room': room, 
                    'error': 'Şifre gereklidir.'
                })
            
            if not room.check_password(password):
                return render(request, 'chat/join_room.html', {
                    'room': room, 
                    'error': 'Yanlış şifre.'
                })
        
        # Şifre doğru veya herkese açık oda - kullanıcıyı ekle
        room.members.add(request.user)
        return redirect('chat:chat_room', room_id=room_id)
    
    # GET isteği - form göster
    if room.room_type == 'private':
        # Özel oda - şifre formu göster
        return render(request, 'chat/join_room.html', {'room': room})
    else:
        # Herkese açık oda - direkt katıl
        room.members.add(request.user)
        return redirect('chat:chat_room', room_id=room_id)

# Create your views here.

class ChatRoomViewSet(viewsets.ModelViewSet):
    """Chat odaları için ViewSet."""
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Oda oluşturulduğunda oluşturan kişiyi üye yap."""
        room = serializer.save()
        room.members.add(self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, pk=None):
        """Bir odaya katılma. Özel odalar için şifre kontrolü yapar."""
        room = self.get_object()
        
        if room.room_type == 'private':
            password = request.data.get('password')
            if not password:
                return Response(
                    {'error': 'Bu özel bir odadır, lütfen şifre girin.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from django.contrib.auth.hashers import check_password
            if not check_password(password, room.password):
                return Response(
                    {'error': 'Girilen şifre yanlış.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Kullanıcı zaten üye değilse ekle
        if request.user not in room.members.all():
            room.members.add(request.user)
            return Response({'status': f'{room.name} odasına başarıyla katıldınız.'}, status=status.HTTP_200_OK)
        
        return Response({'status': 'Zaten bu odanın üyesisiniz.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Odadan ayrıl."""
        room = self.get_object()
        room.members.remove(request.user)
        return Response({'status': 'left'})

class MessageViewSet(viewsets.ModelViewSet):
    """Mesajlar için ViewSet."""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Kullanıcının üye olduğu odalardaki mesajları getir."""
        return Message.objects.filter(
            room__members=self.request.user
        ).select_related('sender', 'room')
    
    def perform_create(self, serializer):
        """Mesaj oluşturulduğunda gönderen kişiyi otomatik ata."""
        serializer.save(sender=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Mesajı sil - sadece mesaj sahibi silebilir."""
        message = self.get_object()
        
        # Sadece mesaj sahibi silebilir
        if message.sender != request.user:
            return Response(
                {'error': 'Bu mesajı silme yetkiniz yok'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete - mesajı silindi olarak işaretle
        message.is_deleted = True
        message.save()
        
        return Response({'status': 'deleted'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def delete_for_me(self, request, pk=None):
        """Mesajı sadece kendim için sil (soft-delete)."""
        message = self.get_object()
        if message.sender == request.user:
            message.is_deleted_for_sender = True
        else:
            message.is_deleted_for_receiver = True
        message.save()
        return Response({'status': 'deleted'})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """Dosya yükleme endpoint'i"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
        
        uploaded_file = request.FILES['file']
        room_id = request.POST.get('room_id')
        
        # Dosya boyutu kontrolü (10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'Dosya boyutu 10MB\'dan büyük olamaz'}, status=400)
        
        # Dosya türü kontrolü
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'application/zip', 'application/x-rar-compressed'
        ]
        
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'error': 'Desteklenmeyen dosya türü'}, status=400)
        
        # Dosya adını güvenli hale getir
        file_name = uploaded_file.name
        file_ext = os.path.splitext(file_name)[1]
        unique_name = f"{uuid.uuid4()}{file_ext}"
        
        # Dosya yolunu oluştur
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files', str(room_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_name)
        
        # Dosyayı kaydet
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # URL oluştur
        file_url = f"/media/chat_files/{room_id}/{unique_name}"
        
        return JsonResponse({
            'success': True,
            'file': {
                'name': file_name,
                'url': file_url,
                'size': uploaded_file.size,
                'type': uploaded_file.content_type
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# API Views
class ChatRoomListCreateView(generics.ListCreateAPIView):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        room.members.add(self.request.user)

class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        return Message.objects.filter(room_id=room_id, is_deleted=False).order_by('created_at')
    
    def perform_create(self, serializer):
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(ChatRoom, id=room_id)
        serializer.save(sender=self.request.user, room=room)

class MessageEditView(generics.UpdateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user:
            return Response({'error': 'Bu mesajı düzenleme yetkiniz yok'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

class MessageDeleteView(generics.DestroyAPIView):
    queryset = Message.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user:
            return Response({'error': 'Bu mesajı silme yetkiniz yok'}, status=status.HTTP_403_FORBIDDEN)
        message.is_deleted = True
        message.save()
        return Response({'status': 'deleted'})

@login_required
def room_management(request, room_id):
    """Oda yönetimi paneli - sadece oda sahibi erişebilir"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Yetki kontrolü
    if not room.can_manage(request.user):
        messages.error(request, 'Bu odayı yönetme yetkiniz yok.')
        return redirect('chat:chat_room', room_id=room_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove_member':
            member_id = request.POST.get('member_id')
            member = get_object_or_404(get_user_model(), id=member_id)
            if member != room.owner:  # Oda sahibini çıkaramaz
                room.members.remove(member)
                messages.success(request, f'{member.username} odadan çıkarıldı.')
        
        elif action == 'update_room':
            room.name = request.POST.get('name', room.name)
            room.description = request.POST.get('description', room.description)
            room.room_type = request.POST.get('room_type', room.room_type)
            
            # Şifre güncelleme
            new_password = request.POST.get('password')
            if new_password:
                room.set_password(new_password)
            
            room.save()
            messages.success(request, 'Oda ayarları güncellendi.')
        
        elif action == 'delete_room':
            room.delete()
            messages.success(request, 'Oda silindi.')
            return redirect('chat:chat_room_list')
        
        elif action == 'add_member':
            username = request.POST.get('new_member_username')
            if username:
                try:
                    user = get_user_model().objects.get(username=username)
                    if user not in room.members.all():
                        room.members.add(user)
                        messages.success(request, f'{username} odaya eklendi.')
                    else:
                        messages.warning(request, f'{username} zaten odanın üyesi.')
                except get_user_model().DoesNotExist:
                    messages.error(request, f'{username} kullanıcısı bulunamadı.')
        
        elif action == 'update_banned_words':
            banned_words = request.POST.get('banned_words', '')
            room.banned_words = banned_words
            room.save()
            messages.success(request, 'Yasaklı kelimeler güncellendi.')
    
    # Oda istatistikleri
    total_messages = Message.objects.filter(room=room).count()
    deleted_messages = Message.objects.filter(room=room, is_deleted=True).count()
    active_members = room.members.filter(is_online=True).count()
    
    context = {
        'room': room,
        'members': room.members.all(),
        'total_messages': total_messages,
        'deleted_messages': deleted_messages,
        'active_members': active_members,
        'room_types': ChatRoom.ROOM_TYPES,
    }
    
    return render(request, 'chat/room_management.html', context)

@login_required
def room_members(request, room_id):
    """Oda üyeleri listesi - AJAX endpoint"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if not room.can_manage(request.user):
        return JsonResponse({'error': 'Yetki yok'}, status=403)
    
    members = []
    for member in room.members.all():
        members.append({
            'id': member.id,
            'username': member.username,
            'is_online': member.is_online,
            'last_seen': member.last_seen.isoformat() if member.last_seen else None,
            'is_owner': room.is_owner(member),
        })
    
    return JsonResponse({'members': members})

@login_required
def room_statistics(request, room_id):
    """Oda istatistikleri - AJAX endpoint"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if not room.can_manage(request.user):
        return JsonResponse({'error': 'Yetki yok'}, status=403)
    
    # Son 7 günlük mesaj sayısı
    from django.utils import timezone
    from datetime import timedelta
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    daily_messages = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        count = Message.objects.filter(
            room=room,
            created_at__date=date.date()
        ).count()
        daily_messages.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    stats = {
        'total_messages': Message.objects.filter(room=room).count(),
        'total_members': room.members.count(),
        'active_members': room.members.filter(is_online=True).count(),
        'daily_messages': daily_messages,
    }
    
    return JsonResponse(stats)

@login_required
def room_recent_messages(request, room_id):
    """Son mesajları getir - AJAX endpoint"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if not room.can_manage(request.user):
        return JsonResponse({'error': 'Yetki yok'}, status=403)
    
    # Son 20 mesajı getir
    recent_messages = Message.objects.filter(
        room=room, 
        is_deleted=False
    ).select_related('sender').order_by('-created_at')[:20]
    
    messages_data = []
    for message in reversed(recent_messages):  # En eskiden en yeniye sırala
        messages_data.append({
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_edited': message.is_edited,
        })
    
    return JsonResponse({'messages': messages_data})

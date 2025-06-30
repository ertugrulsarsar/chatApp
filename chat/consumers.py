import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from channels.auth import AuthMiddlewareStack
from urllib.parse import parse_qs

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat functionality.
    Features:
    - Real-time messaging
    - Typing indicators
    - Message editing/deletion
    - User status updates
    - File sharing support
    - Message history
    - Read receipts
    - Typing indicators
    - User status
    """
    
    async def connect(self):
        try:
            self.room_id = int(self.scope['url_route']['kwargs']['room_id'])
            self.room_group_name = f'chat_{self.room_id}'
            
            # Authentication kontrolü
            self.user = await self.get_user()

            print(f"=== WebSocket Bağlantı Denemesi ===")
            print(f"Kullanıcı: {self.user}")
            print(f"Kimlik Doğrulandı: {self.user.is_authenticated}")
            print(f"Oda ID: {self.room_id}")

            if not self.user.is_authenticated:
                print("[HATA] Kimlik doğrulanmamış kullanıcı. Bağlantı kapatılıyor.")
                await self.close()
                return

            room_exists = await self.room_exists()
            print(f"Oda var mı kontrolü sonucu: {room_exists}")

            if not room_exists:
                print(f"[HATA] {self.room_id} ID'li oda bulunamadı. Bağlantı kapatılıyor.")
                await self.close()
                return

            # Oda üyeliği kontrolü
            is_member = await self.is_room_member()
            print(f"Kullanıcı oda üyesi mi: {is_member}")

            if not is_member:
                print(f"[HATA] Kullanıcı {self.user.username} oda {self.room_id} üyesi değil.")
                await self.close()
                return

            # Kullanıcıyı online yap
            await self.set_user_online()

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            print("=== Bağlantı Başarılı ve Kabul Edildi ===")

        except Exception as e:
            print(f"[KRİTİK HATA] Connect metodunda beklenmedik hata: {e}")
            import traceback
            traceback.print_exc()
            await self.close()

    @database_sync_to_async
    def get_user(self):
        """Kullanıcıyı session'dan al"""
        try:
            # Session'dan user ID'yi al
            session = self.scope.get('session', {})
            user_id = session.get('_auth_user_id')
            
            print(f"[DEBUG] Session: {session}")
            print(f"[DEBUG] User ID from session: {user_id}")
            
            if user_id:
                user = User.objects.get(id=user_id)
                print(f"[DEBUG] User found: {user.username}")
                return user
            else:
                print(f"[DEBUG] Session'da user_id bulunamadı")
                return AnonymousUser()
        except Exception as e:
            print(f"[DEBUG] get_user hatası: {e}")
            return AnonymousUser()
        
    async def disconnect(self, close_code):
        print(f"[DEBUG] Disconnect called with code: {close_code}")
        # Kullanıcıyı offline yap
        await self.set_user_offline()
        # Gruptan ayrıl
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            print(f"[DEBUG] Raw text_data received: {text_data}")
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            print(f"[DEBUG] Mesaj alındı: {message_type} - {text_data_json}")
            
            if message_type == 'message':
                await self.handle_message(text_data_json)
            elif message_type == 'typing_start':
                await self.handle_typing_start(text_data_json)
            elif message_type == 'typing_stop':
                await self.handle_typing_stop(text_data_json)
            elif message_type == 'edit_message':
                await self.handle_edit_message(text_data_json)
            elif message_type == 'delete_message':
                await self.handle_delete_message(text_data_json)
        except Exception as e:
            print(f"[HATA] receive metodunda hata: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_message(self, data):
        try:
            message_content = data.get('message')
            file_info = data.get('file_info')  # Dosya bilgileri

            if not message_content:
                print("[HATA] Mesaj içeriği boş")
                return

            print(f"[DEBUG] Mesaj kaydediliyor: {message_content}")
            if file_info:
                print(f"[DEBUG] Dosya bilgileri: {file_info}")

            # Gelen mesajı veritabanına kaydet
            new_message = await self.save_message(message_content, file_info)

            if not new_message:
                print("[HATA] Mesaj kaydedilemedi")
                return

            print(f"[DEBUG] Mesaj kaydedildi: {new_message.id}")

            # Mesaj verilerini hazırla
            message_data = {
                'id': new_message.id,
                'sender': self.user.username,
                'content': new_message.content,
                'created_at': new_message.created_at.isoformat(),
                'is_edited': False,
                'is_file_message': new_message.is_file_message,  # Dosya mesajı bilgisi
            }

            # Dosya bilgileri varsa ekle
            if new_message.is_file_message:
                message_data['file_info'] = {
                    'name': new_message.file_name,
                    'url': new_message.media_url or '',
                    'size': new_message.file_size,
                    'type': new_message.file_type
                }

            # Gruba yayınla
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )
            print("[DEBUG] Mesaj gruba gönderildi")
        except Exception as e:
            print(f"[HATA] handle_message'da hata: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_edit_message(self, data):
        """Mesaj düzenleme"""
        message_id = data.get('message_id')
        new_content = data.get('content')

        if not message_id or not new_content:
            return

        # Mesajı güncelle
        updated_message = await self.update_message(message_id, new_content)
        
        if updated_message:
            # Gruba yayınla
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_edited',
                    'message': {
                        'id': updated_message.id,
                        'sender': self.user.username,
                        'content': updated_message.content,
                        'created_at': updated_message.created_at.isoformat(),
                        'updated_at': updated_message.updated_at.isoformat(),
                        'is_edited': True,
                    }
                }
            )
    
    async def handle_delete_message(self, data):
        """Mesaj silme"""
        message_id = data.get('message_id')

        if not message_id:
            return

        print(f"[SİLME] Kullanıcı {self.user.username} mesaj {message_id} silmeye çalışıyor")

        # Mesajı sil (soft delete)
        deleted = await self.delete_message(message_id)
        
        if deleted:
            print(f"[SİLME] Mesaj {message_id} başarıyla silindi")
            # Gruba yayınla
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id
                }
            )
        else:
            print(f"[SİLME] Mesaj {message_id} silinemedi - bulunamadı veya yetki yok")
    
    async def handle_typing_start(self, data):
        """Kullanıcı yazmaya başladığında"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_start',
                'username': self.user.username,
            }
        )
    
    async def handle_typing_stop(self, data):
        """Kullanıcı yazmayı durdurduğunda"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_stop',
                'username': self.user.username,
            }
        )
    
    async def chat_message(self, event):
        message_data = event['message']
        
        # Gelen mesajı WebSocket üzerinden client'a gönder
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': message_data
        }))
    
    async def message_edited(self, event):
        """Düzenlenen mesajı gönder"""
        message_data = event['message']
        
        await self.send(text_data=json.dumps({
            'type': 'message_edited',
            'data': message_data
        }))
    
    async def message_deleted(self, event):
        """Silinen mesajı bildir"""
        message_id = event['message_id']
        
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': message_id
        }))
    
    async def typing_start(self, event):
        """Yazıyor göstergesi başlat"""
        await self.send(text_data=json.dumps({
            'type': 'typing_start',
            'username': event['username']
        }))
    
    async def typing_stop(self, event):
        """Yazıyor göstergesi durdur"""
        await self.send(text_data=json.dumps({
            'type': 'typing_stop',
            'username': event['username']
        }))
    
    @database_sync_to_async
    def room_exists(self):
        return ChatRoom.objects.filter(id=self.room_id).exists()

    @database_sync_to_async
    def is_room_member(self):
        """Kullanıcının oda üyesi olup olmadığını kontrol et"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.members.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False
        except Exception as e:
            print(f"[HATA] Üyelik kontrolünde hata: {e}")
            return False

    @database_sync_to_async
    def save_message(self, content, file_info=None):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            
            # Mesaj oluştur
            message_data = {
                'room': room,
                'sender': self.user,
                'content': content,
                'is_file_message': False  # Varsayılan olarak False
            }
            
            # Dosya bilgileri varsa ekle
            if file_info:
                message_data.update({
                    'is_file_message': True,
                    'file_name': file_info.get('name', ''),
                    'file_size': file_info.get('size', 0),
                    'file_type': file_info.get('type', ''),
                    'media_url': file_info.get('url', '')
                })
            
            message = Message.objects.create(**message_data)
            print(f"[DEBUG] Mesaj başarıyla kaydedildi: {message.id}")
            return message
        except ChatRoom.DoesNotExist:
            print(f"[HATA] Oda bulunamadı: {self.room_id}")
            return None
        except Exception as e:
            print(f"[HATA] Mesaj kaydedilirken hata: {e}")
            return None
    
    @database_sync_to_async
    def update_message(self, message_id, new_content):
        """Mesajı güncelle"""
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.user,
                room_id=self.room_id
            )
            message.content = new_content
            message.is_edited = True
            message.save()
            return message
        except Message.DoesNotExist:
            return None
    
    @database_sync_to_async
    def delete_message(self, message_id):
        """Mesajı sil (soft delete)"""
        try:
            message = Message.objects.get(
                id=message_id,
                sender=self.user,
                room_id=self.room_id
            )
            message.is_deleted = True
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def set_user_online(self):
        self.user.is_online = True
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=["is_online", "last_seen"])

    @database_sync_to_async
    def set_user_offline(self):
        self.user.is_online = False
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=["is_online", "last_seen"]) 
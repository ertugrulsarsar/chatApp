from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

@receiver(post_migrate)
def create_general_chat_room(sender, **kwargs):
    # Sinyalin sadece 'chat' uygulaması için çalışmasını sağla
    if sender.name == 'chat':
        from .models import ChatRoom
        User = get_user_model()

        # "Genel Sohbet" odası var mı kontrol et
        if not ChatRoom.objects.filter(name="Genel Sohbet").exists():
            print("Genel Sohbet odası oluşturuluyor...")
            # Odayı oluştur
            general_room = ChatRoom.objects.create(
                name="Genel Sohbet",
                description="Tüm kullanıcıların buluşma noktası.",
                room_type="public" # Herkese açık
            )
            
            # Tüm kullanıcıları bu odaya ekle
            all_users = User.objects.all()
            general_room.members.add(*all_users)
            print(f"'{general_room.name}' odası oluşturuldu ve {all_users.count()} kullanıcı eklendi.") 
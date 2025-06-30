from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class ChatRoom(models.Model):
    """
    Çoklu kullanıcı destekli chat odası modeli.
    - Oda ismi, açıklama ve üyeler.
    - Genişletilebilir yapı.
    """
    ROOM_TYPES = (
        ('public', 'Herkese Açık'),
        ('private', 'Özel (Şifreli)'),
    )

    name = models.CharField(max_length=255, unique=True, verbose_name="Oda Adı")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    owner = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='owned_rooms',
        verbose_name="Oda Sahibi",
        null=True,
        blank=True
    )
    members = models.ManyToManyField(
        'users.CustomUser', 
        related_name='chat_rooms', 
        blank=True,
        verbose_name="Üyeler"
    )
    room_type = models.CharField(
        max_length=10, 
        choices=ROOM_TYPES, 
        default='public',
        verbose_name="Oda Tipi"
    )
    password = models.CharField(
        max_length=128,  # Daha güvenli şifreler için artırıldı
        blank=True, 
        null=True, 
        help_text="Oda tipi 'Özel' ise bu alan zorunludur.",
        verbose_name="Oda Şifresi"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    banned_words = models.TextField(blank=True, null=True, verbose_name="Yasaklı Kelimeler", 
                                   help_text="Virgülle ayrılmış yasaklı kelimeler")

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def is_owner(self, user):
        """Kullanıcının oda sahibi olup olmadığını kontrol et"""
        return self.owner == user

    def can_manage(self, user):
        """Kullanıcının odayı yönetip yönetemeyeceğini kontrol et"""
        return self.is_owner(user) or user.is_superuser

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sohbet Odası"
        verbose_name_plural = "Sohbet Odaları"
        ordering = ['-created_at']

class Message(models.Model):
    """
    Mesaj modeli.
    - Soft-delete desteği (her iki taraf için silinebilir).
    - Mesaj geçmişi, medya, gönderici, oda ilişkisi.
    """
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(blank=True)
    media_url = models.URLField(blank=True, null=True)  # S3 veya lokal medya
    
    # Dosya bilgileri
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # bytes cinsinden
    file_type = models.CharField(max_length=100, blank=True, null=True)  # MIME type
    is_file_message = models.BooleanField(default=False, null=True)  # Dosya mesajı mı?
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # Genel silme durumu
    is_deleted_for_sender = models.BooleanField(default=False)
    is_deleted_for_receiver = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.room}: {self.content[:20]}"
    
    @property
    def is_edited(self):
        """Mesajın düzenlenip düzenlenmediğini kontrol et."""
        return self.updated_at > self.created_at
    
    @property
    def is_deleted_for_user(self, user):
        """Belirli bir kullanıcı için mesajın silinip silinmediğini kontrol et."""
        if user == self.sender:
            return self.is_deleted_for_sender
        else:
            return self.is_deleted_for_receiver

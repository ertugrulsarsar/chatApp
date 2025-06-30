from django.contrib import admin
from .models import ChatRoom, Message
from django.contrib.auth.hashers import make_password

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """Chat odaları admin paneli."""
    list_display = ('name', 'room_type', 'created_at', 'member_count')
    list_filter = ('room_type', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('members',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'room_type')
        }),
        ('Güvenlik (Sadece Özel Odalar için)', {
            'classes': ('collapse',),
            'fields': ('password',),
            'description': "Oda tipi 'Özel' olarak ayarlandığında bu şifre kullanılır. Boş bırakırsanız, yeni bir şifre otomatik oluşturulur veya mevcut şifre korunur."
        }),
        ('Üyeler', {
            'fields': ('members',)
        }),
    )

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Üye Sayısı'
    
    def save_model(self, request, obj, form, change):
        # Eğer bir şifre girilmişse ve hash'lenmemişse, onu hash'le
        if obj.password and not obj.password.startswith('pbkdf2_sha256$'):
             obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Mesajlar admin paneli."""
    list_display = ('sender', 'room', 'content_summary', 'created_at', 'is_deleted')
    list_filter = ('room', 'is_deleted', 'created_at')
    search_fields = ('content', 'sender__username', 'room__name')
    list_per_page = 20
    
    def content_summary(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_summary.short_description = 'Mesaj İçeriği'

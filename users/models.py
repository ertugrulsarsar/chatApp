from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from PIL import Image
import os

class CustomUser(AbstractUser):
    """
    Genişletilebilir kullanıcı modeli.
    - İleriye dönük 2FA, profil resmi, biyografi gibi alanlar kolayca eklenebilir.
    - SOLID prensiplerine uygun, modüler yapı.
    """
    email = models.EmailField(unique=True)
    is_2fa_enabled = models.BooleanField(default=False, help_text="İki faktörlü kimlik doğrulama aktif mi?")
    is_online = models.BooleanField(default=False, verbose_name="Çevrimiçi mi?")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Son görülme")
    
    # Profil resmi alanı
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name="Profil Resmi",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        help_text="Sadece JPG, PNG, GIF ve WebP formatları desteklenir. Maksimum 5MB."
    )
    
    # Biyografi alanı
    bio = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Biyografi",
        help_text="Kendiniz hakkında kısa bir açıklama (maksimum 500 karakter)"
    )
    
    # Doğum tarihi
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Doğum Tarihi"
    )
    
    # Konum
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Konum"
    )

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        """Profil resmini kaydetmeden önce boyutlandır."""
        # Önce kaydet
        super().save(*args, **kwargs)
        
        # Sonra resmi boyutlandır
        try:
            if self.profile_picture:
                self.resize_profile_picture()
        except Exception as e:
            print(f"Profil resmi işleme hatası: {e}")
    
    def resize_profile_picture(self):
        """Profil resmini 300x300 boyutuna getir."""
        try:
            if not self.profile_picture:
                return
                
            img = Image.open(self.profile_picture.path)
            
            # Resim zaten 300x300'den küçükse boyutlandırma yapma
            if img.height <= 300 and img.width <= 300:
                return
                
            # Resmi kare yap ve boyutlandır
            output_size = (300, 300)
            
            # Resmi kare yapmak için crop
            if img.width != img.height:
                # En küçük boyutu al
                min_size = min(img.width, img.height)
                left = (img.width - min_size) // 2
                top = (img.height - min_size) // 2
                right = left + min_size
                bottom = top + min_size
                img = img.crop((left, top, right, bottom))
            
            # Boyutlandır
            img = img.resize(output_size, Image.Resampling.LANCZOS)
            img.save(self.profile_picture.path, quality=85, optimize=True)
            
        except Exception as e:
            print(f"Profil resmi boyutlandırma hatası: {e}")
            # Hata durumunda resmi sil
            try:
                if self.profile_picture:
                    self.profile_picture.delete(save=False)
            except:
                pass
    
    @property
    def profile_picture_url(self):
        """Profil resmi URL'sini döndür."""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            try:
                return self.profile_picture.url
            except:
                pass
        # Default avatar için SVG data URL kullan
        return f"data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDEyMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iMTIwIiBmaWxsPSIjNjY3ZWVhIi8+Cjx0ZXh0IHg9IjYwIiB5PSI3MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjQ4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+{self.username[0].upper()}</dGV4dD4KPC9zdmc+"
    
    @property
    def display_name(self):
        """Görünen ad - full name varsa onu, yoksa username'i döndür."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Kullanıcı kayıt formu."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kullanıcı adınız'
        }),
        help_text="150 karakter veya daha az. Sadece harf, rakam ve @/./+/-/_ karakterleri."
    )
    
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email adresiniz'
        }),
        help_text='Geçerli bir email adresi girin.'
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Şifreniz'
        }),
        help_text="En az 8 karakter olmalı ve tamamen sayısal olmamalı."
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Şifrenizi tekrar girin'
        }),
        help_text="Doğrulama için şifrenizi tekrar girin."
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Kullanıcı profil düzenleme formu."""
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'profile-picture-input'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        help_text="Sadece JPG, PNG, GIF ve WebP formatları desteklenir. Maksimum 5MB."
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adınız'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Soyadınız'
        })
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Kendiniz hakkında kısa bir açıklama...'
        }),
        help_text="Maksimum 500 karakter"
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Şehir, Ülke'
        })
    )
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'location', 'birth_date', 'profile_picture']
    
    def clean_profile_picture(self):
        """Profil resmi validasyonu."""
        profile_picture = self.cleaned_data.get('profile_picture')
        
        if profile_picture:
            # Dosya boyutu kontrolü (5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Dosya boyutu 5MB'dan büyük olamaz.")
        
        return profile_picture

class ChangePasswordForm(forms.Form):
    """Şifre değiştirme formu."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mevcut şifre'
        }),
        label="Mevcut Şifre"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yeni şifre'
        }),
        label="Yeni Şifre",
        help_text="En az 8 karakter olmalı ve tamamen sayısal olmamalı."
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yeni şifre (tekrar)'
        }),
        label="Yeni Şifre (Tekrar)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("Yeni şifreler eşleşmiyor.")
        
        return cleaned_data 
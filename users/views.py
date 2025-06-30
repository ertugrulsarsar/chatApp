from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from .models import CustomUser
from .forms import CustomUserCreationForm, UserProfileForm, ChangePasswordForm
from .serializers import (
    CustomUserSerializer, 
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)

def register(request):
    """Kullanıcı kayıt sayfası."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Hesabınız başarıyla oluşturuldu!')
            return redirect('home')
        else:
            messages.error(request, 'Kayıt sırasında hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    """Kullanıcı giriş sayfası."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Kullanıcıyı online yap
            user.is_online = True
            user.save()
            messages.success(request, f'Hoş geldiniz, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    
    return render(request, 'users/login.html')

@login_required
def user_logout(request):
    """Kullanıcı çıkış işlemi."""
    # Kullanıcıyı offline yap
    request.user.is_online = False
    request.user.last_seen = timezone.now()
    request.user.save()
    
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız.')
    return redirect('home')

@login_required
def profile(request):
    """Kullanıcı profil sayfası."""
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    """Kullanıcı profil düzenleme sayfası."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil bilgileriniz başarıyla güncellendi!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Profil güncellenirken hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    """Şifre değiştirme sayfası."""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password1']
            
            if request.user.check_password(old_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Şifreniz başarıyla değiştirildi!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Mevcut şifre yanlış.')
    else:
        form = ChangePasswordForm()
    
    return render(request, 'users/change_password.html', {'form': form})

# API Views
class CustomTokenObtainPairView(TokenObtainPairView):
    """Özel JWT token view."""
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationView(generics.CreateAPIView):
    """API kullanıcı kayıt view'ı."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Kullanıcı profil API view'ı."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    """Şifre değiştirme API view'ı."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Şifreyi değiştir
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Şifre başarıyla değiştirildi.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_api(request):
    """API logout view'ı."""
    user = request.user
    user.is_online = False
    user.last_seen = timezone.now()
    user.save()
    
    return Response({'message': 'Başarıyla çıkış yapıldı.'}, status=status.HTTP_200_OK)

# Password Reset Views with Rate Limiting
class CustomPasswordResetView(PasswordResetView):
    """Özel password reset view with rate limiting."""
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = '/users/password-reset/done/'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Özel password reset confirm view with rate limiting."""
    template_name = 'users/password_reset_confirm.html'
    success_url = '/users/password-reset-complete/'

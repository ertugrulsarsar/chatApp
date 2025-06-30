from django import forms
from .models import ChatRoom

class ChatRoomForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, help_text="Özel oda için şifre belirleyin.")

    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Oda Adı'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        room_type = cleaned_data.get('room_type')
        password = cleaned_data.get('password')

        if room_type == 'private' and not password:
            self.add_error('password', 'Özel odalar için şifre zorunludur.')

        if room_type == 'public':
            cleaned_data['password'] = ''
            
        return cleaned_data 
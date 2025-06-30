# 💬 ChatApp - Gerçek Zamanlı Chat Uygulaması

Modern ve kapsamlı bir gerçek zamanlı chat uygulaması. Django Channels, WebSocket, REST API ve gelişmiş kullanıcı yönetimi özellikleri ile donatılmış.

## 🚀 Özellikler

### 👥 Kullanıcı Yönetimi
- **Kayıt ve Giriş**: JWT tabanlı kimlik doğrulama
- **Profil Yönetimi**: Avatar yükleme, profil düzenleme
- **Şifre Sıfırlama**: Email ile güvenli şifre sıfırlama
- **Çevrimiçi Durumu**: Gerçek zamanlı çevrimiçi/çevrimdışı gösterimi
- **Son Görülme**: Kullanıcıların son aktivite zamanı

### 🏠 Chat Odaları
- **Çoklu Oda Desteği**: Sınırsız sayıda chat odası
- **Oda Tipleri**: Herkese açık ve özel (şifreli) odalar
- **Oda Katılımı**: Otomatik veya şifre ile katılım
- **Oda Arama**: Hızlı oda bulma

### 💬 Mesajlaşma
- **Gerçek Zamanlı**: WebSocket ile anlık mesajlaşma
- **Dosya Paylaşımı**: Resim, PDF, Word, Excel, ZIP dosyaları
- **Mesaj Düzenleme**: Gönderilen mesajları düzenleme
- **Mesaj Silme**: Kişisel veya genel mesaj silme
- **Mesaj Geçmişi**: Tüm mesaj geçmişini görüntüleme

### ⚙️ Oda Yönetimi
- **Oda Sahipliği**: Her odanın bir sahibi var
- **Üye Yönetimi**: Üye ekleme, çıkarma
- **Oda Ayarları**: Ad, açıklama, tip, şifre değiştirme
- **Moderasyon**: Yasaklı kelimeler, mesaj yönetimi
- **İstatistikler**: Detaylı oda istatistikleri ve grafikler

### 🔧 Teknik Özellikler
- **Django Channels**: WebSocket desteği
- **Redis**: Gerçek zamanlı veri depolama
- **Celery**: Arka plan görevleri
- **AWS S3**: Dosya depolama (opsiyonel)
- **Rate Limiting**: API koruma
- **Responsive Design**: Mobil uyumlu tasarım

## 🛠️ Kurulum

### Gereksinimler
- Python 3.8+
- Redis Server
- PostgreSQL (opsiyonel, SQLite varsayılan)

### 1. Projeyi İndirin
```bash
git clone <repository-url>
cd chatApp
```

### 2. Sanal Ortam Oluşturun
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Veritabanını Hazırlayın
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Süper Kullanıcı Oluşturun
```bash
python manage.py createsuperuser
```

### 6. Redis'i Başlatın
```bash
# Windows
redis-server
# Linux/Mac
sudo service redis start
```

### 7. Sunucuyu Başlatın
```bash
python manage.py runserver
```

## 📁 Proje Yapısı

```
chatApp/
├── chat/                    # Chat uygulaması
│   ├── consumers.py        # WebSocket consumers
│   ├── models.py           # Chat modelleri
│   ├── views.py            # Chat view'ları
│   ├── urls.py             # Chat URL'leri
│   └── templates/          # Chat template'leri
├── users/                   # Kullanıcı uygulaması
│   ├── models.py           # Kullanıcı modelleri
│   ├── views.py            # Kullanıcı view'ları
│   └── templates/          # Kullanıcı template'leri
├── chatApp/                 # Ana proje
│   ├── settings.py         # Proje ayarları
│   ├── routing.py          # WebSocket routing
│   └── urls.py             # Ana URL'ler
├── static/                  # Statik dosyalar
├── media/                   # Yüklenen dosyalar
└── requirements.txt         # Python bağımlılıkları
```

## 🔧 Konfigürasyon

### Environment Variables
`.env` dosyası oluşturun:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0

# Email (şifre sıfırlama için)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (opsiyonel)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=your-region
```

### Redis Konfigürasyonu
`settings.py` dosyasında Redis ayarları:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

## 🚀 Kullanım

### 1. Kayıt ve Giriş
- `/users/register/` - Yeni hesap oluşturma
- `/users/login/` - Giriş yapma
- `/users/password-reset/` - Şifre sıfırlama

### 2. Chat Odaları
- `/chat/` - Tüm odaları görüntüleme
- `/chat/create/` - Yeni oda oluşturma
- `/chat/room/<id>/` - Chat odasına katılma

### 3. Oda Yönetimi
- `/chat/manage/<id>/` - Oda yönetimi (sadece oda sahibi)

## 📊 API Endpoints

### Chat Odaları
- `GET /chat/api/rooms/` - Odaları listele
- `POST /chat/api/rooms/` - Yeni oda oluştur
- `GET /chat/api/rooms/<id>/` - Oda detayları
- `PUT /chat/api/rooms/<id>/` - Oda güncelle
- `DELETE /chat/api/rooms/<id>/` - Oda sil

### Mesajlar
- `GET /chat/api/rooms/<id>/messages/` - Mesajları listele
- `POST /chat/api/rooms/<id>/messages/` - Mesaj gönder
- `PUT /chat/api/messages/<id>/edit/` - Mesaj düzenle
- `DELETE /chat/api/messages/<id>/delete/` - Mesaj sil

### WebSocket
- `ws://localhost:8000/ws/chat/<room_id>/` - Chat odası WebSocket

## 🔒 Güvenlik

### Kimlik Doğrulama
- JWT tabanlı token sistemi
- Otomatik token yenileme
- Güvenli şifre hash'leme

### Yetkilendirme
- Oda sahipliği kontrolü
- Mesaj sahipliği kontrolü
- Admin yetkileri

### Rate Limiting
- API isteklerini sınırlama
- Spam koruması
- DDoS koruması

## 🎨 Tasarım

### Responsive Design
- Mobil uyumlu tasarım
- Modern UI/UX
- Bootstrap ve CSS Grid
- Font Awesome ikonları

### Tema
- Gradient arka planlar
- Glassmorphism efektleri
- Smooth animasyonlar
- Dark/Light mode desteği

## 🧪 Test

### Unit Tests
```bash
python manage.py test
```

### Coverage
```bash
coverage run --source='.' manage.py test
coverage report
```

## 📈 Performans

### Optimizasyonlar
- Database query optimizasyonu
- Redis caching
- Static file compression
- Image optimization

### Monitoring
- Django Debug Toolbar
- Performance logging
- Error tracking

## 🔧 Geliştirme

### Kod Standartları
- PEP 8 uyumlu
- Type hints
- Docstrings
- SOLID prensipleri

### Git Workflow
```bash
git checkout -b feature/new-feature
# Geliştirme yapın
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

## 🚀 Deployment

### Production Ayarları
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
STATIC_ROOT = '/path/to/static/'
MEDIA_ROOT = '/path/to/media/'
```

### Docker (Opsiyonel)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun


## 👨‍💻 Geliştirici

**Ertuğrul Sarsar** - [GitHub](https://github.com/ertugrulsarsar)

## 🙏 Teşekkürler

- Django ve Django Channels ekibi
- Redis geliştiricileri
- Bootstrap ve Font Awesome
- Tüm katkıda bulunanlar

## 📞 İletişim

- Email: ertugrulsarsar@gmail.com
- GitHub: [@ertugrulsarsar](https://github.com/ertugrulsarsar)
- LinkedIn: [Ertuğrul Sarsar](https://linkedin.com/in/ertugrulsarsar)

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın! 
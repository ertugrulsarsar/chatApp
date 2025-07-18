# Generated by Django 5.0.2 on 2025-06-30 19:21

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_customuser_is_online_customuser_last_seen"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="bio",
            field=models.TextField(
                blank=True,
                help_text="Kendiniz hakkında kısa bir açıklama (maksimum 500 karakter)",
                max_length=500,
                null=True,
                verbose_name="Biyografi",
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="birth_date",
            field=models.DateField(blank=True, null=True, verbose_name="Doğum Tarihi"),
        ),
        migrations.AddField(
            model_name="customuser",
            name="location",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Konum"
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="profile_picture",
            field=models.ImageField(
                blank=True,
                help_text="Sadece JPG, PNG, GIF ve WebP formatları desteklenir. Maksimum 5MB.",
                null=True,
                upload_to="profile_pictures/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"]
                    )
                ],
                verbose_name="Profil Resmi",
            ),
        ),
    ]

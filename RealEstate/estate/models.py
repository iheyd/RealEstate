from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('client', 'Клиент'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class RealEstate(models.Model):
    STATUS_CHOICES = (
        ('available', 'Свободно'),
        ('rented', 'Сдано'),
    )
    title = models.CharField("Название", max_length=150)
    description = models.TextField("Описание")
    area = models.FloatField("Площадь (кв.м)")
    floor = models.IntegerField("Этаж", default=1)
    location = models.CharField("Местоположение", max_length=200)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='available')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Администратор", related_name="estates")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def is_reserved(self):
        return self.viewingrequest_set.filter(status__in=['pending', 'confirmed']).exists()


class RealEstateImage(models.Model):
    """Модель для хранения нескольких фотографий одного объекта"""
    estate = models.ForeignKey(RealEstate, on_delete=models.CASCADE, related_name='images', verbose_name="Объект")
    image = models.ImageField("Фотография", upload_to='estates/%Y/%m/')
    is_main = models.BooleanField("Главное фото", default=False)

    def __str__(self):
        return f"Фото для {self.estate.title}"


class ViewingRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидание'),
        ('confirmed', 'Подтверждено'),
        ('rejected', 'Отклонено'),
    )
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests', verbose_name="Клиент")
    estate = models.ForeignKey(RealEstate, on_delete=models.CASCADE, verbose_name="Объект")
    request_date = models.DateTimeField("Дата запроса", default=timezone.now)
    viewing_date = models.DateTimeField("Желаемая дата просмотра")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Запрос от {self.client.username} на {self.estate.title}"


class LeaseAgreement(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contracts', verbose_name="Клиент")
    estate = models.ForeignKey(RealEstate, on_delete=models.CASCADE, verbose_name="Объект")
    start_date = models.DateField("Начало аренды")
    end_date = models.DateField("Конец аренды")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Договор: {self.estate.title} - {self.client.username}"


# ==========================================
# СИГНАЛЫ (Автоматическое создание профиля)
# ==========================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Если создается суперпользователь, даем ему роль админа, иначе клиента
        role = 'admin' if instance.is_superuser else 'client'
        Profile.objects.create(user=instance, role=role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
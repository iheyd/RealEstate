from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = (
        ('client', 'Клиент'),
        ('owner', 'Владелец'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    is_approved = models.BooleanField("Подтвержден", default=True)
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")

    def __str__(self):
        if self.role == 'owner':
            status = "✅" if self.is_approved else "⏳ На модерации"
            return f"{self.user.username} (Владелец) {status}"
        return f"{self.user.username} (Клиент)"

    @property
    def can_login(self):
        """Может ли пользователь войти в систему."""
        return self.role == 'client' or self.is_approved


class RealEstate(models.Model):
    STATUS_CHOICES = (
        ('available', 'Свободно'),
        ('rented', 'Сдано'),
    )
    UTILITIES_CHOICES = (
        ('included', 'Включена'),
        ('not_included', 'Не включена'),
    )
    PREPAYMENT_CHOICES = (
        ('none', 'Отсутствует'),
        ('1_month', '1 месяц'),
        ('3_months', '3 месяца'),
    )
    LEASE_TERM_CHOICES = (
        ('month', 'Месяц'),
        ('from_month', 'От месяца'),
        ('from_3_months', 'От трех месяцев'),
        ('from_half_year', 'От полугода'),
        ('from_year', 'От года'),
    )
    title = models.CharField("Название", max_length=150)
    description = models.TextField("Описание")
    area = models.FloatField("Площадь (кв.м)")
    floor = models.IntegerField("Этаж", default=1)
    location = models.CharField("Местоположение", max_length=200)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='available')
    utilities_included = models.CharField("Оплата ЖКХ", max_length=20, choices=UTILITIES_CHOICES, default='included')
    deposit = models.DecimalField("Залог", max_digits=12, decimal_places=0, default=0)
    prepayment = models.CharField("Предоплата", max_length=20, choices=PREPAYMENT_CHOICES, default='1_month')
    lease_term = models.CharField("Срок аренды", max_length=20, choices=LEASE_TERM_CHOICES, default='from_year')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", related_name="estates")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def main_image(self):
        """Главное фото (is_main=True), иначе первое по порядку."""
        return self.images.filter(is_main=True).first() or self.images.first()

    @property
    def ordered_images(self):
        """Фото в порядке: главное первым, остальные по ID."""
        images = list(self.images.all())
        main = self.main_image
        if main:
            images.remove(main)
            images.insert(0, main)
        return images

    def is_reserved(self):
        return self.viewingrequest_set.filter(status__in=['pending', 'confirmed']).exists()


class RealEstateImage(models.Model):
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
        ('cancelled', 'Отменено'),
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
from django.contrib import admin
from .models import Profile, RealEstate, RealEstateImage, ViewingRequest, LeaseAgreement

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)

class RealEstateImageInline(admin.TabularInline):
    model = RealEstateImage
    extra = 1  # Показывать одну пустую строку для добавления нового фото

@admin.register(RealEstate)
class RealEstateAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'status', 'owner')
    list_filter = ('status', 'location', 'price')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    inlines = [RealEstateImageInline]  # Подключаем загрузку фото прямо в форму объявления

@admin.register(ViewingRequest)
class ViewingRequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'estate', 'viewing_date', 'status')
    list_filter = ('status', 'viewing_date')

@admin.register(LeaseAgreement)
class LeaseAgreementAdmin(admin.ModelAdmin):
    list_display = ('client', 'estate', 'start_date', 'end_date')
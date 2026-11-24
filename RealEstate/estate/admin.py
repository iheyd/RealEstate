from django.contrib import admin
from .models import Profile, RealEstate, RealEstateImage, ViewingRequest, LeaseAgreement


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_approved', 'phone')
    list_filter = ('role', 'is_approved')
    search_fields = ('user__username', 'user__email')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.role == 'client':
            return ('is_approved',)
        return ()


class RealEstateImageInline(admin.TabularInline):
    model = RealEstateImage
    extra = 1


@admin.register(RealEstate)
class RealEstateAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'status', 'owner')
    list_filter = ('status', 'location')
    search_fields = ('title', 'description')
    inlines = [RealEstateImageInline]


@admin.register(ViewingRequest)
class ViewingRequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'estate', 'viewing_date', 'status')
    list_filter = ('status', 'viewing_date')


@admin.register(LeaseAgreement)
class LeaseAgreementAdmin(admin.ModelAdmin):
    list_display = ('client', 'estate', 'start_date', 'end_date')
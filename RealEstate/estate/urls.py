from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Публичные страницы
    path('', views.home, name='home'),
    path('listings/', views.listings, name='listings'),
    path('listing/<int:estate_id>/', views.listing_detail, name='listing_detail'),
    path('reviews/', views.reviews, name='reviews'),

    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Личный кабинет
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.dashboard_profile, name='dashboard_profile'),
    path('dashboard/estates/', views.dashboard_estates, name='dashboard_estates'),
    path('dashboard/requests/', views.dashboard_requests, name='dashboard_requests'),
    path('dashboard/deals/', views.dashboard_deals, name='dashboard_deals'),

    # Управление заявками на просмотр
    path('dashboard/requests/<int:request_id>/confirm/', views.confirm_request, name='confirm_request'),
    path('dashboard/requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('dashboard/requests/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),

    # Модерация (только для суперпользователей)
    path('dashboard/moderation/', views.dashboard_moderation, name='dashboard_moderation'),
    path('dashboard/moderation/<int:profile_id>/approve/', views.approve_owner, name='approve_owner'),
    path('dashboard/moderation/<int:profile_id>/reject/', views.reject_owner, name='reject_owner'),

    # Действия с объектами
    path('add-estate/', views.add_estate, name='add_estate'),
    path('edit-estate/<int:estate_id>/', views.edit_estate, name='edit_estate'),
    path('request-viewing/<int:estate_id>/', views.request_viewing, name='request_viewing'),

    # Обратная связь
    path('feedback-success/', views.feedback_success, name='feedback_success'),
]
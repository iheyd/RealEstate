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
    path('login/', auth_views.LoginView.as_view(template_name='estate/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Личный кабинет (Dashboard)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.dashboard_profile, name='dashboard_profile'),
    path('dashboard/estates/', views.dashboard_estates, name='dashboard_estates'),
    path('dashboard/requests/', views.dashboard_requests, name='dashboard_requests'),
    path('dashboard/deals/', views.dashboard_deals, name='dashboard_deals'),

    # Действия с объектами и заявками
    path('add-estate/', views.add_estate, name='add_estate'),
    path('edit-estate/<int:estate_id>/', views.edit_estate, name='edit_estate'),
    path('request-viewing/<int:estate_id>/', views.request_viewing, name='request_viewing'),

    # Обратная связь
    path('feedback-success/', views.feedback_success, name='feedback_success'),
]
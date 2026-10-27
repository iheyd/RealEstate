from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-estate/', views.add_estate, name='add_estate'),
    path('request-viewing/<int:estate_id>/', views.request_viewing, name='request_viewing'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('feedback/', views.feedback, name='feedback'),
]
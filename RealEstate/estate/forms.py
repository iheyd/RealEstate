from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, RealEstate, ViewingRequest, RealEstateImage


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Почта')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    phone = forms.CharField(max_length=20, required=False, label='Номер телефона')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('phone',)


class RealEstateForm(forms.ModelForm):
    class Meta:
        model = RealEstate
        fields = ['title', 'description', 'area', 'floor', 'location', 'price', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Опишите преимущества объекта...'}),
        }


class RealEstateImageForm(forms.ModelForm):
    class Meta:
        model = RealEstateImage
        fields = ['image', 'is_main']


class ViewingRequestForm(forms.ModelForm):
    class Meta:
        model = ViewingRequest
        fields = ['viewing_date']
        widgets = {
            'viewing_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=100, label='Ваше имя')
    email = forms.EmailField(label='Ваш Email')
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Сообщение')
from django import forms
from django.contrib.auth.models import User
from .models import RealEstate, ViewingRequest, Profile, LeaseAgreement

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Подтвердите пароль")
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label="Роль")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            raise forms.ValidationError("Пароли не совпадают!")
        return cleaned_data

class RealEstateForm(forms.ModelForm):
    class Meta:
        model = RealEstate
        fields = ['title', 'description', 'area', 'location', 'price']

class ViewingRequestForm(forms.ModelForm):
    class Meta:
        model = ViewingRequest
        fields = ['estate', 'viewing_date']

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']

class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
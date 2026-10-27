from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.forms import modelformset_factory

from .models import Profile, RealEstate, ViewingRequest, LeaseAgreement, RealEstateImage
from .forms import (
    UserRegisterForm, UserEditForm, ProfileEditForm,
    RealEstateForm, ViewingRequestForm, FeedbackForm, RealEstateImageForm
)


def home(request):
    return render(request, 'estate/home.html')


def listings(request):
    estates = RealEstate.objects.filter(status='available')
    location = request.GET.get('location')
    area_min = request.GET.get('area_min')
    price_min = request.GET.get('price_min')

    if location:
        estates = estates.filter(location__icontains=location)
    if area_min:
        estates = estates.filter(area__gte=float(area_min))
    if price_min:
        estates = estates.filter(price__gte=float(price_min))

    estates = estates.order_by('-created_at')
    return render(request, 'estate/listings.html', {'estates': estates})


def listing_detail(request, estate_id):
    """Детальная страница одного объявления"""
    estate = get_object_or_404(RealEstate, id=estate_id)
    return render(request, 'estate/listing_detail.html', {'estate': estate})


def reviews(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            send_mail(
                subject=f"Отзыв от {form.cleaned_data['name']}",
                message=form.cleaned_data['message'],
                from_email=form.cleaned_data['email'],
                recipient_list=['admin@example.com'],
                fail_silently=False,
            )
            return redirect('feedback_success')
    else:
        form = FeedbackForm()
    return render(request, 'estate/reviews.html', {'form': form})


def feedback_success(request):
    return render(request, 'estate/form.html', {
        'title': 'Спасибо!',
        'success_message': 'Ваше сообщение успешно отправлено.'
    })


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get('phone')
            if phone:
                user.profile.phone = phone
                user.profile.save()

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}! Вы успешно зарегистрированы.')
                return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'estate/register.html', {'form': form})


@login_required
def dashboard(request):
    return redirect('dashboard_profile')


@login_required
def dashboard_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('dashboard_profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    return render(request, 'estate/dashboard_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'active_tab': 'profile',
    })


@login_required
def dashboard_estates(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('dashboard_profile')

    estates = RealEstate.objects.filter(owner=request.user)
    return render(request, 'estate/dashboard_estates.html', {
        'estates': estates,
        'active_tab': 'estates',
    })


@login_required
def dashboard_requests(request):
    if request.user.profile.role == 'admin':
        requests_list = ViewingRequest.objects.filter(estate__owner=request.user)
    else:
        requests_list = ViewingRequest.objects.filter(client=request.user)

    return render(request, 'estate/dashboard_requests.html', {
        'requests_list': requests_list,
        'active_tab': 'requests',
    })


@login_required
def dashboard_deals(request):
    deals = LeaseAgreement.objects.filter(client=request.user)
    return render(request, 'estate/dashboard_deals.html', {
        'deals': deals,
        'active_tab': 'deals',
    })


@login_required
def add_estate(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Только администраторы могут добавлять объекты.')
        return redirect('dashboard')

    ImageFormSet = modelformset_factory(RealEstateImage, form=RealEstateImageForm, extra=3)

    if request.method == 'POST':
        form = RealEstateForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=RealEstateImage.objects.none())

        if form.is_valid() and formset.is_valid():
            estate = form.save(commit=False)
            estate.owner = request.user
            estate.save()

            # Сохраняем изображения
            for img_form in formset:
                if img_form.cleaned_data.get('image'):
                    image = img_form.save(commit=False)
                    image.estate = estate
                    image.save()

            messages.success(request, 'Объект и фотографии успешно добавлены!')
            return redirect('dashboard_estates')
    else:
        form = RealEstateForm()
        formset = ImageFormSet(queryset=RealEstateImage.objects.none())

    return render(request, 'estate/form_estate.html', {
        'form': form,
        'formset': formset,
        'title': 'Добавить объект'
    })


@login_required
def edit_estate(request, estate_id):
    estate = get_object_or_404(RealEstate, id=estate_id, owner=request.user)
    ImageFormSet = modelformset_factory(RealEstateImage, form=RealEstateImageForm, extra=1)

    if request.method == 'POST':
        form = RealEstateForm(request.POST, instance=estate)
        formset = ImageFormSet(request.POST, request.FILES, queryset=estate.images.all())

        if form.is_valid() and formset.is_valid():
            estate = form.save()

            # Сохраняем изображения
            instances = formset.save(commit=False)
            for image in instances:
                image.estate = estate
                image.save()

            # Удаляем отмеченные для удаления
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, 'Объект успешно обновлен!')
            return redirect('dashboard_estates')
    else:
        form = RealEstateForm(instance=estate)
        formset = ImageFormSet(queryset=estate.images.all())

    return render(request, 'estate/form_estate.html', {
        'form': form,
        'formset': formset,
        'title': 'Редактировать объект',
        'estate': estate
    })


@login_required
def request_viewing(request, estate_id):
    estate = get_object_or_404(RealEstate, id=estate_id)
    if request.method == 'POST':
        form = ViewingRequestForm(request.POST)
        if form.is_valid():
            viewing = form.save(commit=False)
            viewing.client = request.user
            viewing.estate = estate
            viewing.save()
            try:
                send_mail(
                    subject='Новый запрос на просмотр',
                    message=f'Клиент {request.user.username} ({request.user.email}) хочет посмотреть объект "{estate.title}" на дату {viewing.viewing_date}.',
                    from_email='noreply@prostranstvo.ru',
                    recipient_list=[estate.owner.email],
                    fail_silently=False,
                )
                messages.success(request, 'Запрос отправлен! Уведомление отправлено владельцу.')
            except Exception:
                messages.warning(request, 'Запрос сохранен, но возникла ошибка при отправке email.')
            return redirect('dashboard_requests')
    else:
        form = ViewingRequestForm()

    return render(request, 'estate/form.html', {'form': form, 'title': f'Запрос на просмотр: {estate.title}'})
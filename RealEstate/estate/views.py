from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.contrib import messages

from .models import Profile, RealEstate, ViewingRequest, LeaseAgreement, RealEstateImage
from .forms import (
    UserRegisterForm, UserEditForm, ProfileEditForm,
    RealEstateForm, ViewingRequestForm, FeedbackForm
)


# ==========================================
# Кастомный LoginView с проверкой модерации
# ==========================================
class CustomLoginView(LoginView):
    template_name = 'estate/login.html'

    def form_valid(self, form):
        user = form.get_user()

        if user.is_superuser:
            return super().form_valid(form)

        if hasattr(user, 'profile') and not user.profile.can_login:
            messages.error(
                self.request,
                'Ваш аккаунт владельца находится на модерации. '
                'Вы не сможете войти в систему, пока администратор не подтвердит вашу регистрацию.'
            )
            form.add_error(None, "Аккаунт на модерации")
            return self.form_invalid(form)

        return super().form_valid(form)


# ==========================================
# Декоратор для суперпользователей
# ==========================================
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Доступ только для администраторов.')
            return redirect('dashboard_profile')
        return view_func(request, *args, **kwargs)

    return wrapper


# ==========================================
# Публичные страницы
# ==========================================
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
        try:
            estates = estates.filter(area__gte=float(area_min))
        except ValueError:
            pass
    if price_min:
        try:
            estates = estates.filter(price__gte=float(price_min))
        except ValueError:
            pass

    estates = estates.order_by('-created_at')
    return render(request, 'estate/listings.html', {'estates': estates})


def listing_detail(request, estate_id):
    estate = get_object_or_404(RealEstate, id=estate_id)

    context = {'estate': estate}

    # Если пользователь авторизован — проверяем его заявки на этот объект
    if request.user.is_authenticated:
        user_confirmed = ViewingRequest.objects.filter(
            client=request.user,
            estate=estate,
            status='confirmed'
        ).first()

        user_pending = ViewingRequest.objects.filter(
            client=request.user,
            estate=estate,
            status='pending'
        ).first()

        context['user_confirmed_request'] = user_confirmed
        context['user_pending_request'] = user_pending

    return render(request, 'estate/listing_detail.html', context)


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


# ==========================================
# Регистрация
# ==========================================
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get('phone')
            role = form.cleaned_data.get('role')

            Profile.objects.create(
                user=user,
                role=role,
                phone=phone,
                is_approved=(role == 'client')
            )

            if role == 'owner':
                messages.info(
                    request,
                    'Спасибо за регистрацию! Ваш аккаунт отправлен на модерацию. '
                    'Вы сможете войти в систему после подтверждения администратором.'
                )
                return redirect('login')
            else:
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Добро пожаловать, {username}!')
                    return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'estate/register.html', {'form': form})


# ==========================================
# Личный кабинет
# ==========================================
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
    if request.user.profile.role != 'owner' or not request.user.profile.is_approved:
        messages.error(request, 'Этот раздел доступен только подтвержденным владельцам.')
        return redirect('dashboard_profile')

    estates = RealEstate.objects.filter(owner=request.user)
    return render(request, 'estate/dashboard_estates.html', {
        'estates': estates,
        'active_tab': 'estates',
    })


@login_required
def dashboard_requests(request):
    if request.user.profile.role == 'owner' and request.user.profile.is_approved:
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


# ==========================================
# Модерация
# ==========================================
@admin_required
def dashboard_moderation(request):
    pending = Profile.objects.filter(role='owner', is_approved=False).select_related('user')
    approved = Profile.objects.filter(role='owner', is_approved=True).select_related('user')

    return render(request, 'estate/dashboard_moderation.html', {
        'pending_owners': pending,
        'approved_owners': approved,
        'active_tab': 'moderation',
    })


@admin_required
def approve_owner(request, profile_id):
    if request.method != 'POST':
        return redirect('dashboard_moderation')

    profile = get_object_or_404(Profile, id=profile_id, role='owner')
    profile.is_approved = True
    profile.save()

    messages.success(request, f'Владелец {profile.user.username} одобрен и получил доступ к системе.')
    return redirect('dashboard_moderation')


@admin_required
def reject_owner(request, profile_id):
    if request.method != 'POST':
        return redirect('dashboard_moderation')

    profile = get_object_or_404(Profile, id=profile_id, role='owner')
    username = profile.user.username
    profile.user.delete()

    messages.success(request, f'Заявка владельца {username} отклонена. Аккаунт удален.')
    return redirect('dashboard_moderation')


# ==========================================
# ДОБАВЛЕНИЕ ОБЪЕКТА
# ==========================================
@login_required
def add_estate(request):
    if request.user.profile.role != 'owner' or not request.user.profile.is_approved:
        messages.error(request, 'Только подтвержденные владельцы могут добавлять объекты.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = RealEstateForm(request.POST)
        if form.is_valid():
            estate = form.save(commit=False)
            estate.owner = request.user
            estate.save()

            images = request.FILES.getlist('images')
            for index, img in enumerate(images):
                RealEstateImage.objects.create(
                    estate=estate,
                    image=img,
                    is_main=(index == 0)
                )

            messages.success(request, 'Объект и фотографии успешно добавлены!')
            return redirect('dashboard_estates')
    else:
        form = RealEstateForm()

    return render(request, 'estate/form_estate.html', {
        'form': form,
        'title': 'Добавить объект'
    })


# ==========================================
# РЕДАКТИРОВАНИЕ ОБЪЕКТА
# ==========================================
@login_required
def edit_estate(request, estate_id):
    estate = get_object_or_404(RealEstate, id=estate_id, owner=request.user)

    if request.user.profile.role != 'owner' or not request.user.profile.is_approved:
        messages.error(request, 'У вас нет прав на редактирование этого объекта.')
        return redirect('dashboard_estates')

    if request.method == 'POST':
        form = RealEstateForm(request.POST, instance=estate)
        if form.is_valid():
            estate = form.save()

            delete_ids = request.POST.getlist('delete_image')
            if delete_ids:
                estate.images.filter(id__in=delete_ids).delete()

            estate.images.update(is_main=False)

            main_ids = request.POST.getlist('main_image')
            if main_ids:
                estate.images.filter(id__in=main_ids).update(is_main=True)
            elif estate.images.exists():
                estate.images.first().is_main = True
                estate.images.first().save()

            images = request.FILES.getlist('images')
            for img in images:
                RealEstateImage.objects.create(estate=estate, image=img, is_main=False)

            messages.success(request, 'Объект успешно обновлен!')
            return redirect('dashboard_estates')
    else:
        form = RealEstateForm(instance=estate)

    return render(request, 'estate/form_estate.html', {
        'form': form,
        'title': 'Редактировать объект',
        'estate': estate,
        'existing_images': estate.images.all()
    })


# ==========================================
# Запрос на просмотр
# ==========================================
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
                    message=f'Клиент {request.user.username} хочет посмотреть объект "{estate.title}" на дату {viewing.viewing_date}.',
                    from_email='noreply@prostranstvo.ru',
                    recipient_list=[estate.owner.email],
                    fail_silently=False,
                )
                messages.success(request, 'Запрос отправлен!')
            except Exception:
                messages.warning(request, 'Запрос сохранен, но email не отправлен.')
            return redirect('dashboard_requests')
    else:
        form = ViewingRequestForm()

    return render(request, 'estate/form.html', {'form': form, 'title': f'Запрос на просмотр: {estate.title}'})


# ==========================================
# Управление заявками на просмотр
# ==========================================
@login_required
def confirm_request(request, request_id):
    """Подтверждение запроса на просмотр"""
    viewing_request = get_object_or_404(ViewingRequest, id=request_id)

    if viewing_request.estate.owner != request.user:
        messages.error(request, 'У вас нет прав для управления этой заявкой.')
        return redirect('dashboard_requests')

    if request.method == 'POST':
        viewing_request.status = 'confirmed'
        viewing_request.save()

        try:
            send_mail(
                subject=f'Ваш запрос на просмотр "{viewing_request.estate.title}" подтверждён',
                message=f'Здравствуйте, {viewing_request.client.get_full_name() or viewing_request.client.username}!\n\n'
                        f'Ваш запрос на просмотр объекта "{viewing_request.estate.title}" подтверждён.\n'
                        f'Дата просмотра: {viewing_request.viewing_date.strftime("%d.%m.%Y в %H:%M")}.\n\n'
                        f'Свяжитесь с владельцем для уточнения деталей.',
                from_email='noreply@prostranstvo.ru',
                recipient_list=[viewing_request.client.email],
                fail_silently=False,
            )
            messages.success(request, 'Заявка подтверждена. Уведомление отправлено клиенту.')
        except Exception:
            messages.warning(request, 'Заявка подтверждена, но не удалось отправить email.')

        return redirect('dashboard_requests')

    return redirect('dashboard_requests')


@login_required
def reject_request(request, request_id):
    """Отклонение запроса на просмотр"""
    viewing_request = get_object_or_404(ViewingRequest, id=request_id)

    if viewing_request.estate.owner != request.user:
        messages.error(request, 'У вас нет прав для управления этой заявкой.')
        return redirect('dashboard_requests')

    if request.method == 'POST':
        viewing_request.status = 'rejected'
        viewing_request.save()

        try:
            send_mail(
                subject=f'Ваш запрос на просмотр "{viewing_request.estate.title}" отклонён',
                message=f'Здравствуйте, {viewing_request.client.get_full_name() or viewing_request.client.username}!\n\n'
                        f'К сожалению, ваш запрос на просмотр объекта "{viewing_request.estate.title}" отклонён.\n'
                        f'Вы можете подать запрос на другой объект.\n\n'
                        f'С уважением, команда сайта.',
                from_email='noreply@prostranstvo.ru',
                recipient_list=[viewing_request.client.email],
                fail_silently=False,
            )
            messages.success(request, 'Заявка отклонена. Уведомление отправлено клиенту.')
        except Exception:
            messages.warning(request, 'Заявка отклонена, но не удалось отправить email.')

        return redirect('dashboard_requests')

    return redirect('dashboard_requests')


@login_required
def cancel_request(request, request_id):
    """Отмена резерва (доступно клиенту и владельцу объекта)"""
    viewing_request = get_object_or_404(ViewingRequest, id=request_id)

    is_client = viewing_request.client == request.user
    is_owner = viewing_request.estate.owner == request.user

    if not (is_client or is_owner):
        messages.error(request, 'У вас нет прав для отмены этой заявки.')
        return redirect('dashboard_requests')

    if viewing_request.status != 'confirmed':
        messages.error(request, 'Отменить можно только подтверждённую заявку.')
        return redirect('dashboard_requests')

    if request.method == 'POST':
        viewing_request.status = 'cancelled'
        viewing_request.save()

        if is_client:
            recipient = viewing_request.estate.owner
            subject = f'Клиент отменил просмотр объекта "{viewing_request.estate.title}"'
            message = (
                f'Здравствуйте, {recipient.get_full_name() or recipient.username}!\n\n'
                f'Клиент {viewing_request.client.get_full_name() or viewing_request.client.username} '
                f'отменил подтверждённый просмотр объекта "{viewing_request.estate.title}".\n'
                f'Объект снова доступен для бронирования другими клиентами.\n\n'
                f'Дата запланированного просмотра: {viewing_request.viewing_date.strftime("%d.%m.%Y в %H:%M")}.\n\n'
                f'С уважением, команда сайта.'
            )
            messages.success(request, 'Резерв отменён. Владелец уведомлён.')
        else:
            recipient = viewing_request.client
            subject = f'Просмотр объекта "{viewing_request.estate.title}" отменён владельцем'
            message = (
                f'Здравствуйте, {recipient.get_full_name() or recipient.username}!\n\n'
                f'Владелец отменил подтверждённый просмотр объекта "{viewing_request.estate.title}".\n'
                f'Вы можете подать запрос на другой объект.\n\n'
                f'Дата запланированного просмотра: {viewing_request.viewing_date.strftime("%d.%m.%Y в %H:%M")}.\n\n'
                f'С уважением, команда сайта.'
            )
            messages.success(request, 'Бронирование отменено. Клиент уведомлён.')

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@prostranstvo.ru',
                recipient_list=[recipient.email],
                fail_silently=False,
            )
        except Exception:
            messages.warning(request, 'Статус изменён, но не удалось отправить email-уведомление.')

        return redirect('dashboard_requests')

    return redirect('dashboard_requests')
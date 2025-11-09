from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
import random
import string
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from .forms import OrderForm, CustomUserCreationForm

def _get_cart(request):
    """Вспомогательная функция для получения корзины"""
    if not request.session.session_key:
        request.session.create()
    
    cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

def _generate_username(email, first_name, last_name):
    """Генерация уникального имени пользователя на основе email и имени"""
    base_username = f"{first_name.lower()}_{last_name.lower()}"
    username = base_username
    
    # Если username уже существует, добавляем случайные цифры
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1
    
    return username

def _generate_random_password(length=12):
    """Генерация случайного пароля"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for i in range(length))

@transaction.atomic
def order_create(request):
    cart = _get_cart(request)
    
    if not cart.items.exists():
        messages.error(request, 'Ваша корзина пуста')
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        
        if form.is_valid():
            # Извлекаем данные из формы
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            address = form.cleaned_data['address']
            postal_code = form.cleaned_data['postal_code']
            city = form.cleaned_data['city']
            create_account = form.cleaned_data['create_account']
            
            user = None
            
            # Создаем пользователя, если отмечена галочка и пользователь не авторизован
            if create_account and not request.user.is_authenticated:
                try:
                    # Проверяем, существует ли пользователь с таким email
                    existing_user = User.objects.filter(email=email).first()
                    
                    if existing_user:
                        # Пользователь уже существует, используем его
                        user = existing_user
                        messages.info(request, f'Найден существующий аккаунт с email {email}. Вы можете войти в него.')
                    else:
                        # Создаем нового пользователя
                        username = _generate_username(email, first_name, last_name)
                        password = _generate_random_password()
                        
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name
                        )
                        
                        # Авторизуем пользователя
                        auth_user = authenticate(request, username=username, password=password)
                        if auth_user:
                            login(request, auth_user)
                            messages.success(request, f'Аккаунт создан! Ваш логин: {username}')
                except Exception as e:
                    messages.warning(request, f'Не удалось создать аккаунт: {str(e)}')
            
            # Если пользователь уже авторизован, используем его
            elif request.user.is_authenticated:
                user = request.user
            
            # Создание заказа
            order = Order.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                postal_code=postal_code,
                city=city
            )
            
            # Перенос товаров из корзины в заказ
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
            
            # Очистка корзины
            cart.items.all().delete()
            
            messages.success(request, 'Ваш заказ успешно создан!')
            return redirect('orders:order_created', order_id=order.id)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        # Предзаполняем форму данными авторизованного пользователя
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = OrderForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'orders/create.html', context)

def order_created(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Проверяем, принадлежит ли заказ текущему пользователю
    if request.user.is_authenticated and order.user != request.user:
        messages.warning(request, 'Этот заказ не принадлежит вашему аккаунту.')
    
    context = {
        'order': order,
    }
    return render(request, 'orders/created.html', context)

def order_list(request):
    # Показываем заказы только авторизованного пользователя
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created')
    else:
        orders = Order.objects.none()
        messages.info(request, 'Сделайте ваш первый заказ!')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/list.html', context)

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Проверяем права доступа
    if not request.user.is_authenticated or (order.user != request.user and not request.user.is_staff):
        messages.error(request, 'У вас нет доступа к этому заказу.')
        return redirect('orders:order_list')
    
    context = {
        'order': order,
    }
    return render(request, 'orders/detail.html', context)
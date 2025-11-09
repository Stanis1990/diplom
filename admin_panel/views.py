from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from products.models import Product
from orders.models import Order, OrderItem
from .forms import ProductForm, LoginForm
from django.db.models import Sum


def is_admin(user):
    return user.is_authenticated and user.is_staff

# user_passes_test - это декоратор в Django, который используется для ограничения доступа 
# к представлениям (views) на основе пользовательских проверок.

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Статистика заказов
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    # Общая статистика
    total_orders = Order.objects.count() # Кол-во заказов
    total_products = Product.objects.count() # Кол-во товаров
    total_revenue = OrderItem.objects.aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0 # Сумма всех продаж
    
    # Статистика по периодам
    orders_today = Order.objects.filter(created__date=today).count()
    orders_week = Order.objects.filter(created__date__gte=week_ago).count()
    orders_month = Order.objects.filter(created__date__gte=month_ago).count()
    
    revenue_today = OrderItem.objects.filter(
        order__created__date=today
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    revenue_week = OrderItem.objects.filter(
        order__created__date__gte=week_ago
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    revenue_month = OrderItem.objects.filter(
        order__created__date__gte=month_ago
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    # Статусы заказов
    order_statuses = Order.objects.values('status').annotate(
        count=Count('id')
    )
    
    popular_products_data = OrderItem.objects.values(
        'product__id', 'product__name'
    ).annotate(
        total_ordered=Sum('quantity'), # Кол-во проданных товаров
        total_revenue=Sum(F('quantity') * F('price'))  # Выручка
    ).order_by('-total_ordered')[:10]
    
    context = {
        'total_orders': total_orders, # Всего заказов
        'total_revenue': total_revenue, # Общая выручка
        'total_products': total_products, # Товаров в каталоге
        'orders_today': orders_today, # Заказов за день
        'orders_week': orders_week, # Заказов за неделю
        'orders_month': orders_month, # Заказов за месяц
        'revenue_today': revenue_today, # Общая выручка за день
        'revenue_week': revenue_week, # Общая выручка за неделю
        'revenue_month': revenue_month, # Общая выручка за месяц
        'order_statuses': order_statuses, # Статусы заказов
        'popular_products_data': popular_products_data, # Популярные товары
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_orders(request):
    orders = Order.objects.all().order_by('-created')
    # Статусы заказов
    order_statuses = Order.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'order_statuses': order_statuses
    }
    return render(request, 'admin_panel/orders.html', context)

@login_required
@user_passes_test(is_admin)
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} обновлен')
            return redirect('admin_panel:order_detail', order_id=order.id)
    
    context = {
        'order': order,
    }
    return render(request, 'admin_panel/order_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    context = {
        'products': products,
    }
    return render(request, 'admin_panel/products.html', context)

@login_required
@user_passes_test(is_admin)
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успешно создан')
            return redirect('admin_panel:products')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin_panel/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен')
            return redirect('admin_panel:products')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'admin_panel/product_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удален')
        return redirect('admin_panel:products')
    
    context = {
        'product': product,
    }
    return render(request, 'admin_panel/product_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_statistics(request):
    period = request.GET.get('period', 'week')
    
    # Определяем период
    today = timezone.now().date()
    if period == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)
    elif period == 'month':
        start_date = today - timedelta(days=30)
        end_date = today + timedelta(days=1)
    elif period == 'year':
        start_date = today - timedelta(days=365)
        end_date = today + timedelta(days=1)
    else:
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)
    
    # Статистика по товарам
    product_stats = OrderItem.objects.filter(
        order__created__range=[start_date, end_date]
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')
    
    # Общая статистика за период
    total_orders_period = Order.objects.filter(
        created__range=[start_date, end_date]
    ).count()
    
    total_revenue_period = OrderItem.objects.filter(
        order__created__range=[start_date, end_date]
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    # Статистика для сравнения периодов
    orders_today = Order.objects.filter(created__date=today).count()
    orders_week = Order.objects.filter(created__date__gte=today - timedelta(days=7)).count()
    orders_month = Order.objects.filter(created__date__gte=today - timedelta(days=30)).count()
    
    revenue_today = OrderItem.objects.filter(
        order__created__date=today
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    revenue_week = OrderItem.objects.filter(
        order__created__date__gte=today - timedelta(days=7)
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    revenue_month = OrderItem.objects.filter(
        order__created__date__gte=today - timedelta(days=30)
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    # Количество товаров за периоды
    order_items_today = OrderItem.objects.filter(
        order__created__date=today
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    order_items_week = OrderItem.objects.filter(
        order__created__date__gte=today - timedelta(days=7)
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    order_items_month = OrderItem.objects.filter(
        order__created__date__gte=today - timedelta(days=30)
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'product_stats': product_stats,
        'period': period,
        'total_orders_period': total_orders_period,
        'total_revenue_period': total_revenue_period,
        'start_date': start_date,
        'end_date': end_date - timedelta(days=1),
        # Для сравнения периодов
        'orders_today': orders_today,
        'orders_week': orders_week,
        'orders_month': orders_month,
        'revenue_today': revenue_today,
        'revenue_week': revenue_week,
        'revenue_month': revenue_month,
        'order_items_today': order_items_today,
        'order_items_week': order_items_week,
        'order_items_month': order_items_month,
    }
    return render(request, 'admin_panel/statistics.html', context)

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_panel:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('admin_panel:dashboard')
            else:
                messages.error(request, 'Неверные учетные данные или недостаточно прав')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin_panel/login.html', context)

@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('admin_panel:login')
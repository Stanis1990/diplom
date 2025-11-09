from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Product
from .models import Cart, CartItem

def _get_cart(request):
    if not request.session.session_key:
        request.session.create()
    
    cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

def cart_detail(request):
    cart = _get_cart(request)
    context = {
        'cart': cart,
    }
    return render(request, 'cart/detail.html', context)

@require_POST
def cart_add(request, product_id):
    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id, is_available=True)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Количество товара "{product.name}" увеличено')
    else:
        messages.success(request, f'Товар "{product.name}" добавлен в корзину')
    
    return redirect('products:home')

@require_POST
def cart_remove(request, product_id):
    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()
        messages.success(request, f'Товар "{product.name}" удален из корзины')
    except CartItem.DoesNotExist:
        messages.error(request, 'Товар не найден в корзине')
    
    return redirect('cart:cart_detail')

@require_POST
def cart_update(request, product_id):
    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'Количество товара "{product.name}" обновлено')
        else:
            cart_item.delete()
            messages.success(request, f'Товар "{product.name}" удален из корзины')
    except CartItem.DoesNotExist:
        messages.error(request, 'Товар не найден в корзине')
    
    return redirect('cart:cart_detail')
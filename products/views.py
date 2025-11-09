from django.shortcuts import render, get_object_or_404
from .models import Product
from django.db.models import Q


def home(request):
    products = Product.objects.filter(is_available=True)
    
    # Обработка поискового запроса
    search_query = request.GET.get('search', '')
    if search_query:
        # поиск без учета регистра по полю name и description
        # icontains - поиск вхождения без учета регистра
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'products': products,
        'search_query': search_query,
    }
    return render(request, 'home.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {
        'product': product,
    }
    return render(request, 'products/detail.html', context)
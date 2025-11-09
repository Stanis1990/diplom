from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    path('orders/', views.admin_orders, name='orders'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='order_detail'),
    
    path('products/', views.admin_products, name='products'),
    path('products/create/', views.admin_product_create, name='product_create'),
    path('products/<int:product_id>/edit/', views.admin_product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.admin_product_delete, name='product_delete'),
    
    path('statistics/', views.admin_statistics, name='statistics'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
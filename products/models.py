from django.db import models
from django.urls import reverse


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='products/%Y/%m/%d/', verbose_name='Изображение')
    is_available = models.BooleanField(default=True, verbose_name='Доступен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.slug])
    
    @property
    def total_ordered(self):
        """Общее количество заказанного товара"""
        from orders.models import OrderItem
        return OrderItem.objects.filter(product=self).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def total_revenue(self):
        """Общая выручка от товара"""
        from orders.models import OrderItem
        return OrderItem.objects.filter(product=self).aggregate(
            total=models.Sum(models.F('quantity') * models.F('price'))
        )['total'] or 0
    
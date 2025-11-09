from django import template

register = template.Library()

@register.filter
def dictsum(value, key):
    """Суммирует значения по ключу в списке словарей"""
    if not value:
        return 0
    return sum(item.get(key, 0) for item in value)

@register.filter
def div(value, arg):
    """Делит значение на аргумент"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
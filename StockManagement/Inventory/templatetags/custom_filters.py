from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={'class': css})

@register.filter(name='get_class')
def get_class(value):
    return value.__class__.__name__

@register.filter(name='get_stock_type')
def get_stock_type(stock):
    return stock.__class__.__name__
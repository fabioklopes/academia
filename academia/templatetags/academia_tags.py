from django import template

register = template.Library()

@register.filter(name='format_grau')
def format_grau(value):
    if value == 0:
        return "Nenhum Grau"
    elif value == 1:
        return "1 Grau"
    else:
        return f"{value} Graus"

@register.filter(name='lookup')
def lookup(value, arg):
    return value.get(arg)

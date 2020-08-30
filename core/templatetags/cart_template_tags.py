from django import template
from core.models import Order

register = template.Library()

@register.filter
def cart_item_count(session_id):
    # if user.is_authenticated:
    qs = Order.objects.filter(session_id=session_id, ordered=False)
    if qs.exists():
        return qs[0].items.count()
    return 0

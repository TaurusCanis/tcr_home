from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon, Refund, Address, ItemVariant, Customer, ItemVariantFiles

def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)

make_refund_accepted.short_description = 'Update orders to refund granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer',
        'session_id',
        'ordered',
        'being_delivered',
        'received',
        'refund_requested',
        'refund_granted',
        'billing_address',
        'shipping_address',
        'payment',
        'coupon']
    list_display_links = ['customer',
        'billing_address',
        'shipping_address',
        'payment',
        'coupon']
    list_filter = ['customer',
        'ordered',
        'being_delivered',
        'received',
        'refund_requested',
        'refund_granted']
    search_fields = [
        'customer__last_name',
        'ref_code'
    ]
    actions = [make_refund_accepted]

class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'customer',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]

    list_filter = ['address_type', 'default', 'country']

    search_fields = ['customer', 'street_address', 'apartment_address', 'zip']

admin.site.register(Item)
admin.site.register(ItemVariant)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
admin.site.register(Customer)
admin.site.register(ItemVariantFiles)

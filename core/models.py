from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField
from localflavor.us.models import USStateField
import math
from decimal import *

# Create your models here.

CATEGORY_CHOICES = {
    ('C', 'Clothing'),
    ('P', 'Posters'),
    ('M', 'Mugs')
}

LABEL_CHOICES = {
    ('P', 'primary'),
    ('S', 'seconary'),
    ('D', 'danger')
}

ADDRESS_CHOICES = {
    ('B', 'billing'),
    ('S', 'shipping'),
}

class Item(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, blank=True, null=True)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, blank=True, null=True)
    slug = models.SlugField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    printful_product_id = models.IntegerField(blank=True, null=True)
    thumbnail_url = models.CharField(max_length=300, blank=True, null=True)
    printful_name = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.printful_name

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add_to_cart", kwargs={
            'slug': self.slug
        })

    def remove_from_cart(self):
        return reverse("core:remove_from_cart", kwargs={
            'slug': self.slug
        })

class ItemVariant(models.Model):
    title = models.CharField(max_length=200)
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    printful_variant_id = models.IntegerField(blank=True, null=True)
    printful_item_variant_id = models.IntegerField(blank=True, null=True)
    retail_price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=2000, blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title

class ItemVariantFiles(models.Model):
    file_id = models.IntegerField(blank=True, null=True)
    item_variant = models.ForeignKey('ItemVariant', on_delete=models.CASCADE)
    url = models.CharField(max_length=200, null=True)
    file_name = models.CharField(max_length=400)

    def __str__(self):
        return self.file_name

class OrderItem(models.Model):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                          on_delete=models.CASCADE, blank=True, null=True)
    # customer = models.ForeignKey("Customer", on_delete=models.CASCADE, default="")
    session_id = models.CharField(max_length=20, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(ItemVariant, on_delete=models.CASCADE) #change from Item
    quantity = models.IntegerField(default=1)

    # def __str__(self):
    #     return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.retail_price

    # def get_total_item_discount_price(self):
    #     return self.quantity * self.item.discount_price

    # def get_amount_saved(self):
    #     return self.get_total_item_price() - self.get_total_item_discount_price()

    def get_final_price(self):
        # if self.item.discount_price:
        #     return self.get_total_item_discount_price()
        # else:
        #     return self.get_total_item_price()

        return self.get_total_item_price()

class Order(models.Model):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, null=True, blank=True)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    session_id = models.CharField(max_length=20, blank=True, null=True)
    printful_order_id = models.IntegerField(blank=True, null=True)
    tax = models.CharField(max_length=100, blank=True, null=True)
    vat = models.CharField(max_length=100, blank=True, null=True)
    subtotal = models.CharField(max_length=100, blank=True, null=True)
    grand_total = models.CharField(max_length=100, blank=True, null=True)
    shipping_cost = models.CharField(max_length=100, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        "Address", related_name="billing_address", on_delete=models.SET_NULL, blank=True, null=True
    )
    shipping_address = models.ForeignKey(
        "Address", related_name="shipping_address", on_delete=models.SET_NULL, blank=True, null=True
    )
    payment = models.ForeignKey(
        "Payment", on_delete=models.SET_NULL, blank=True, null=True
    )
    coupon = models.ForeignKey("Coupon", on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    donation_added = models.BooleanField(default=False)

    # 1. Item added to cart
    # 2. Adding billing address
    # (Failed checkout)
    # 3. payment
    # (preprocessing, processing, packaging, etc.)
    # 4. Being delivered
    # 5. Received
    # 6. Refunds

    # def __str__(self):
    #     return self.session_id

    def get_subtotal(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return round(total, 2)

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= Decimal(self.coupon.amount)
        # if self.tax:
        #     total += float(self.tax)
        # if self.vat:
        #     total += float(self.vat)
        if self.shipping_cost:
            total += Decimal(self.shipping_cost)
        return round(total, 2)

class Customer(models.Model):
    first_name = models.CharField(max_length=40, blank=True, null=True)
    last_name = models.CharField(max_length=40, blank=True, null=True)
    email_address = models.CharField(max_length=200, blank=True, null=True)
    # phone_number = models.CharField(max_length=20, blank=True, null=True)

    # def __str__(self):
    #     return self.first_name + " " + self.last_name
        # return self.first_name 

class Address(models.Model):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    # customer_name = models.CharField(max_length=20, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=20, blank=True, null=True)
    street_address = models.CharField(max_length=200)
    apartment_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = USStateField(default="CT")
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    # def __str__(self):
    #     return self.session_id

    class Meta:
        verbose_name_plural = 'Addresses'

class Payment(models.Model):
    # stripe_charge_id = models.CharField(max_length=50)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    braintree_transaction_id = models.CharField(max_length=100)

    # def __str__(self):
    #     return self.session_id

class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"

class MailingListSubscriber(models.Model):
    first_name = models.CharField(max_length=25)
    email_address = models.EmailField()
    date_subscribed = models.DateTimeField(auto_now_add=True)

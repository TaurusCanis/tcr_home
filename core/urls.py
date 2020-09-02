from django.urls import path
from .views import (
    item_list,
    OrderSummaryView,
    CheckoutView,
    HomeView,
    ItemDetailView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    AddCoupon,
    RequestRefund,
    ProductsPage,
    OrderConfirmation,
    braintree_client_token,
    braintree_create_purchase,
    order_confirmation_page,
    tandc,
    pp,
    returns_policy
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # path('checkout/', CheckoutView.as_view(), name='checkout'),
    # path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    # # path('add_to_cart/<slug>/', add_to_cart, name='add_to_cart'),
    # path('add_to_cart/<item_variant_id>/<printful_product_id>/', add_to_cart, name='add_to_cart'),
    # # path('remove_from_cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    # path('remove_from_cart/<item_variant_id>/', remove_from_cart, name='remove_from_cart'),
    # path('order_summary/', OrderSummaryView.as_view(), name='order_summary'),
    # # path('remove_single_item_from_cart/<slug>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),
    # path('remove_single_item_from_cart/<item_variant_id>/<printful_product_id>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),
    # path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    # path('payment/', PaymentView.as_view(), name='payment'),
    # path('add_coupon/', AddCoupon.as_view(), name='add_coupon'),
    # path('request_refund/', RequestRefund.as_view(), name='request_refund'),
    # path('products_page/', ProductsPage.as_view(), name='products_page'),
    # path('order_confirmation/', OrderConfirmation.as_view(), name='order_confirmation'),
    # path('braintree_client_token/', braintree_client_token, name='braintree_client_token'),
    # path('braintree_create_purchase/', braintree_create_purchase, name='braintree_create_purchase'),
    # path('order_confirmation_page/', order_confirmation_page, name='order_confirmation_page'),
    # path('tandc/', tandc, name='tandc'),
    # path('pp/', pp, name='pp'),
    # path('returns_policy/', returns_policy, name='returns_policy')
]

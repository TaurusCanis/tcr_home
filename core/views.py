from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, ItemVariant, ItemVariantFiles, MailingListSubscriber, Customer
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm, CouponForm, RefundForm, MailingListForm
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import random
import string
import requests
import json
import base64
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives


import stripe
import braintree

# def parking_page(request):
#     return render(request, "parking_page.html")

# BRAINTREE SANDBOX INTEGRATION
# gateway = braintree.BraintreeGateway(
#     braintree.Configuration(
#         braintree.Environment.Sandbox,
#         merchant_id=settings.BRAINTREE_SANDBOX_MERCHANT_ID,
#         public_key=settings.BRAINTREE_SANDBOX_PUBLIC_KEY,
#         private_key=settings.BRAINTREE_SANDBOX_PRIVATE_KEY
#     )
# )

# Braintree Production Integration
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Production,
        merchant_id=settings.BRAINTREE_PRODUCTION_MERCHANT_ID,
        public_key=settings.BRAINTREE_PRODUCTION_PUBLIC_KEY,
        private_key=settings.BRAINTREE_PRODUCTION_PRIVATE_KEY
    )
)

def braintree_client_token(request):
    client_token = gateway.client_token.generate()
    print("client_token: ", client_token)
    data = { 'token': client_token }
    return JsonResponse(data)

def braintree_create_purchase(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    print("body: ", body)

    nonce_from_the_client = body['nonce_from_the_client']
    device_data_from_the_client = body['device_data_from_the_client']
    order_id = body["order_id"]
    amount = body['amount']

    print("device_data_from_the_client: ", device_data_from_the_client)

    billing_address = body["billing"]["street_address"]
    billing_address_2 = body["billing"]["extended_address"]
    billing_city = body["billing"]["locality"]
    billing_state = body["billing"]["region"]
    billing_postal_code = body["billing"]["postal_code"]
    billing_country_code = body["billing"]["country_code_alpha2"]

    shipping_address = body["shipping"]["street_address"]
    shipping_address_2 = body["shipping"]["extended_address"]
    shipping_city = body["shipping"]["locality"]
    shipping_state = body["shipping"]["region"]
    shipping_postal_code = body["shipping"]["postal_code"]
    shipping_country_code = body["shipping"]["country_code_alpha2"]

    order = Order.objects.get(session_id=request.session['id'], ordered=False)
    items_in_order = OrderItem.objects.filter(session_id=order.session_id)
    print("ITEMS_IN_ORDER****: ", items_in_order)

    line_items = []
    for order_item in items_in_order:
        line_items.append({
            "kind": 'debit',
            "name": order_item.item.title,
            "product_code": order_item.item.id,
            "quantity": order_item.quantity,
            "unit_amount": order_item.item.retail_price,
            "total_amount": order_item.quantity * order_item.item.retail_price
        })
    print("post")
    try:
        ref_code = create_ref_code()
        print("ref_code: ", ref_code)
        print("ref_code type: ", type(ref_code))
        print("try")

        result = gateway.transaction.sale({
            "amount": amount,
            "merchant_account_id": "TaurusCanisRex_instant",
            "payment_method_nonce": nonce_from_the_client,
            "device_data": device_data_from_the_client,
            "customer": {
                "first_name": body['customer']['first_name'],
                "last_name": body['customer']['last_name'],
                # "phone": customer_phone,
                "email": body['customer']['email_address']
            },
            "line_items": line_items,
            "billing": {
                # "first_name": billing_first_name,
                # "last_name": billing_last_name,
                "street_address": billing_address,
                "extended_address": billing_address_2,
                "locality": billing_city,
                "region": billing_state,
                "postal_code": billing_postal_code,
                "country_code_alpha2": billing_country_code
            },
            "shipping": {
                # "first_name": shipping_first_name,
                # "last_name": shipping_last_name,
                "street_address": shipping_address,
                "extended_address": shipping_address_2,
                "locality": shipping_city,
                "region": shipping_state,
                "postal_code": shipping_postal_code,
                "country_code_alpha2": shipping_country_code
            },
            "options": {
                "submit_for_settlement": True
            },
        })

        if result.is_success:
            #create payment
            payment = Payment()
            # payment.stripe_charge_id = charge['id'] #he used charge['id']
            payment.session_id = request.session['id']
            payment.amount = order.get_total()
            order = order
            braintree_transaction_id = result.transaction.id
            payment.save()
            print("payment")

            #assign payment to order

            order_items = order.items.filter(session_id = request.session["id"])
            print("ORDER_ITEMS: ", order_items)
            order_items.update(ordered=True)
            print("ORDER_ITEMS: ", order_items)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = ref_code
            order.save()
            print("save")

            # update_printful_order(order.printful_order_id)
            # send_confirmation_email(order)

            print("result: ", result)
            successful_order = Order.objects.filter(id=order_id)[0]
            print("successful_order: ", successful_order)
            successful_order.ordered = True
            successful_order.save()

            # print("request.session['id']: ", request.session['id'])
            # request.session['id'] = None
            # request.session.modified = True
            request.session.flush()

            return JsonResponse({ "url": "order_confirmation_page" })
        else:
            print("error")
            return JsonResponse({ "url": "error_page" })
    except Exception as e:
        # Send email to self
        print("exception!!")
        print("error: ", e)
        messages.warning(request, "An error has ocurred. We have been notified. You have not been charged.")
        return redirect("/")


#STRIPE INTEGRATION
# stripe.api_key = settings.STRIPE_SECRET_KEY
# stripe.api_key = 'sk_test_sYyZfPMDiefqOPb1I6yZvHzM00GXAujNFH'

store = settings.PRINTFUL_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def create_session_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def item_list(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "home-page.html", context)

def is_valid_form(values):
    print("IS VALID")
    print(values)
    valid = True
    for field in values:
        if field == '':
            valid = False
        print(field)
    return valid

def order_confirmation_page(request):
    print("order_confirmation_page")
    order_id = request.POST.get("order_id")

    order = Order.objects.get(id = order_id)

    send_confirmation_email(order)

    return render(request, "order_confirmation_page.html", { "order": order })

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(session_id=self.request.session['id'], ordered=False)
            print("ORDER: ", order)
            # form = CheckoutForm()
            context = {
                # "form": form,
                'coupon_form': CouponForm(),
                "order": order,
                'DISPLAY_COUPON_FORM': True
            }
        except ObjectDoesNotExist:
            print("ALPHA")
            messages.info(self.request, "You do not have an active order.")
            return redirect("core:products_page")

        if order.customer:
            customer = Customer.objects.get(id = order.customer.id)
            print("customer: ", customer)

            data = {
                "customer_id": customer.id,
                "email_address": customer.email_address,
                "first_name": customer.first_name,
                "last_name": customer.last_name
            }

            shipping_address_qs = Address.objects.filter(
                    session_id=self.request.session['id'],
                    address_type = 'S',
                    customer = customer
                    # default = True
                )


            print("shipping_address_qs: ", shipping_address_qs)

            if shipping_address_qs.exists():
                # context.update({ 'default_shipping_address': shipping_address_qs[0] })
                data.update({
                    "shipping_address": shipping_address_qs[0].street_address,
                    "shipping_address2": shipping_address_qs[0].apartment_address,
                    "shipping_country": shipping_address_qs[0].country,
                    "shipping_city": shipping_address_qs[0].city,
                    "shipping_state": shipping_address_qs[0].state,
                    "shipping_zip": shipping_address_qs[0].zip
                })



# same_billing_address = forms.BooleanField(required=False)
# set_default_shipping = forms.BooleanField(required=False)
# use_default_shipping = forms.BooleanField(required=False)
# set_default_billing = forms.BooleanField(required=False)
# use_default_billing = forms.BooleanField(required=False)

            billing_address_qs = Address.objects.filter(
                    session_id=self.request.session['id'],
                    address_type = 'B',
                    customer = customer
                    # default = True
                )


            if billing_address_qs.exists():
                # context.update({ 'default_billing_address': billing_address_qs[0] })
                data.update({
                    "billing_address": billing_address_qs[0].street_address,
                    "billing_address2": billing_address_qs[0].apartment_address,
                    "billing_country": billing_address_qs[0].country,
                    "billing_city": billing_address_qs[0].city,
                    "billing_state": billing_address_qs[0].state,
                    "billing_zip": billing_address_qs[0].zip
                })

            print("billing_address_qs: ", billing_address_qs)
            print("data: ", data)
            form = CheckoutForm(data)
            print("form is valid?: ", form.is_valid())
            print("form: ", form)

        else:
            print("ELSE")
            form = CheckoutForm()

        context.update({ "form": form })

        print("checkout context: ", context)
        print("CHECKOUT PAGE")
        return render(self.request, "checkout-page.html", context)


    def post(self, *args, **kwargs):
        print('post')
        form = CheckoutForm(self.request.POST or None)

        print("form.is_valid(): ", form.is_valid())
        print("form.errors(): ", form.errors)
        try:
            print("try")
            order = Order.objects.get(session_id=self.request.session['id'], ordered=False)
            print("order: ", order)
            if form.is_valid():
                print("valid")
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                customer_id = form.cleaned_data.get('customer_id')
                print("customer_id: ", customer_id)
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        session_id=self.request.session['id'],
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    if order.customer is None:
                        customer = Customer(
                            first_name = form.cleaned_data.get(
                            'first_name'),
                            last_name = form.cleaned_data.get(
                            'last_name'),
                            email_address = form.cleaned_data.get(
                            'email_address'),
                            # phone_number = form.cleaned_data.get(
                            # 'shipping_address')
                        )
                        customer.save()
                        order.customer = customer
                        order.save()
                    else:
                        customer = Customer.objects.get(id = order.customer.id)
                    shipping_address = order.shipping_address

                    if shipping_address is None:
                        shipping_address = Address()

                    # customer_name = form.cleaned_data.get(
                    #     'customer_name')
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_city = form.cleaned_data.get('shipping_city')
                    shipping_state = form.cleaned_data.get('shipping_state')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    print("ORDER.CUSTOMER: ", order.customer)

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        # shipping_address = Address(
                        shipping_address.customer = customer
                        shipping_address.session_id=self.request.session['id']
                        shipping_address.street_address=shipping_address1
                        shipping_address.apartment_address=shipping_address2
                        shipping_address.state = shipping_state
                        shipping_address.city = shipping_city
                        shipping_address.country=shipping_country
                        shipping_address.zip=shipping_zip
                        shipping_address.address_type='S'
                        # )
                        shipping_address.save()


                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                billing_address = order.billing_address

                if billing_address is None:
                    billing_address = Address()

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        session_id=self.request.session['id'],
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_city = form.cleaned_data.get('billing_city')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        # billing_address = Address(
                        billing_address.customer = customer
                        billing_address.session_id=self.request.session['id']
                        billing_address.street_address=billing_address1
                        billing_address.apartment_address=billing_address2
                        billing_address.city = billing_city
                        billing_address.country=billing_country
                        billing_address.zip=billing_zip
                        billing_address.address_type='B'
                        # )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                print("order: ", order)
                print("order items: ", order.items)
                # print("billing_address: ", billing_address)

                print("order.printful_order_id: ", order.printful_order_id)
                if order.printful_order_id is not None:
                    res = create_printful_order(order, shipping_address)
                    print("create_printful_order RES: ", res)
                else:
                    print("printful order exists")
                    # update_printful_order()
                    pass
                # payment_option = form.cleaned_data.get('payment_option')

                return redirect('core:payment')

                # if payment_option == 'S':
                #     return redirect('core:payment', payment_option='stripe')
                # elif payment_option == 'P':
                #     return redirect('core:payment', payment_option='paypal')
                # else:
                #     messages.warning(
                #         self.request, "Invalid payment option selected")
                #     return redirect('core:checkout')
        except ObjectDoesNotExist:
            print("BETA")
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")

class PaymentView(View):
    def get(self, *args, **kwargs):
        print("merchant_id= ", settings.BRAINTREE_SANDBOX_MERCHANT_ID)
        print("public_key= ", settings.BRAINTREE_SANDBOX_PUBLIC_KEY)
        print("private_key= ", settings.BRAINTREE_SANDBOX_PRIVATE_KEY)

        order = Order.objects.get(session_id=self.request.session['id'], ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'stripe_key': 'pk_test_4tNiwpsFHEX7N7hon7bpW4kE00saVfxboZ'
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        print("request: ", self.request.POST)
        order = Order.objects.get(session_id=self.request.session['id'], ordered=False)
        # token = self.request.POST.get('stripeToken')
        # token = 'tok_visa'
        # amount = int(order.get_total() * 100)
        print("post")
        try:
            ref_code = create_ref_code()
            print("ref_code: ", ref_code)
            print("ref_code type: ", type(ref_code))
            print("try")
            # `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token
            # charge = stripe.Charge.create(
            #     amount=amount, #cents
            #     currency="usd",
            #     source=token
            # )
            # print("charge: ", charge)

            if charge['status'] == 'succeeded':
                #create payment
                payment = Payment()
                # payment.stripe_charge_id = charge['id'] #he used charge['id']
                payment.session_id = self.request.session['id']
                payment.amount = order.get_total()
                payment.save()
                print("payment")

                #assign payment to order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = ref_code
                order.save()
                print("save")

                # self.request.session['id'] = None 
                # request.session.modified = True

                # print("request.session['id']: ", request.session['id'])
                # request.session['id'] = None
                # request.session.modified = True
                # request.session.flush()
                # print("request.session['id']: ", request.session['id'])

                # update_printful_order(order.printful_order_id)
                # send_confirmation_email(order)


                messages.success(self.request, "Your order was successful!")
                return redirect("core:order_confirmation")
            else:
                messages.error(self.request, "Your card was not accepted.")
                return redirect("core:payment")
                # return redirect("core:payment/stripe")

        # except stripe.error.CardError as e:
        #     # Since it's a decline, stripe.error.CardError will be caught

        #     body = e.json_body
        #     err = body.get('error', {})
        #     messages.warning(self.request, f"{err.get('message')}")

        # except stripe.error.RateLimitError as e:
        #     # Too many requests made to the API too quickly
        #     messages.warning(self.request, "Rate limit error")
        #     return redirect("/")
        # except stripe.error.InvalidRequestError as e:
        #     # Invalid parameters were supplied to Stripe's API
        #     messages.warning(self.request, "Invalid parameters")
        #     return redirect("/")
        # except stripe.error.AuthenticationError as e:
        #     # Authentication with Stripe's API failed
        #     # (maybe you changed API keys recently)
        #     messages.warning(self.request, "Not authenticated")
        #     return redirect("/")
        # except stripe.error.APIConnectionError as e:
        #     # Network communication with Stripe failed
        #     messages.warning(self.request, "Network Error")
        #     return redirect("/")
        # except stripe.error.StripeError as e:
        #     # Display a very generic error to the user, and maybe send
        #     # yourself an email
        #     messages.warning(self.request, "Something went wrong. You were not charged. Please try again.")
        #     return redirect("/")
        except Exception as e:
            # Send email to self
            messages.warning(self.request, "An error has ocurred. We have been notified.")
            return redirect("/")

class OrderConfirmation(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(session_id=self.request.session['id'], ordered=True)
        context = { 'order': order }
        del self.request.session['id']
        return render(self.request, "order_confirmation.html", context)

def send_confirmation_email(order):
    html_template = get_template("order_confirmation.html")

    html_content = html_template.render({ "order": order })

    # email = EmailMessage(
    #     'Order Confirmation - TaurusCanis Rex',
    #     "Message",
    #     'admin@tauruscanisrex.com',
    #     [order.customer.email_address],
    #     reply_to=['admin@tauruscanisrex.com'],
    #     # headers={'Message-ID': 'foo'},
    #     html_message=html_content
    # )

    # email.attach_alternative(html_content, "text/html")
    # email.send()
    send_mail(
        'Order Confirmation - TaurusCanisRex.com',
        'Here is the message.',
        'admin@tauruscanisrex.com',
        [order.customer.email_address],
        fail_silently=False,
        html_message=html_content
    )
    return

def update_printful_order(order_id):
    printful_api_base = 'https://api.printful.com/'
    key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
    b64Val = base64.b64encode(key_bytes)
    key_decoded = b64Val.decode('utf-8')
    headers = {
        'content-type': 'application/json',
        'Authorization': "Basic %s" %key_decoded
    }
    url = printful_api_base + "orders/" + str(order_id) + "/confirm"

    try:
        response = requests.post(url, headers=headers)
        response_json = response.json()
        # print("response_json: ", response_json)

        return True, response
    except requests.exceptions.RequestException as e:
        print("ERROR: When submitting order with requests, "
              "error message: %s" % str(e))
        return False, e


def delete_order(order_id):
    printful_api_base = 'https://api.printful.com/'
    key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
    b64Val = base64.b64encode(key_bytes)
    key_decoded = b64Val.decode('utf-8')
    headers = {
        'content-type': 'application/json',
        'Authorization': "Basic %s" %key_decoded
    }
    url = printful_api_base + "orders/" + order_id

    try:
        response = requests.delete(url, headers=headers)
        # print("response = ", response.status_code, response.text)
        response_json = response.json()
        # print("response_json: ", response_json)

        return True, response
    except requests.exceptions.RequestException as e:
        print("ERROR: When submitting order with requests, "
              "error message: %s" % str(e))
        return False, e


def get_products():
    printful_api_base = 'https://api.printful.com/'
    key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
    b64Val = base64.b64encode(key_bytes)
    key_decoded = b64Val.decode('utf-8')
    headers = {
        'content-type': 'application/json',
        'Authorization': "Basic %s" %key_decoded
    }
    url = printful_api_base + "store/products"

    response = requests.get(url, headers=headers)
    data = response.json()['result']
    return data

def get_orders():
    printful_api_base = 'https://api.printful.com/'
    key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
    b64Val = base64.b64encode(key_bytes)
    key_decoded = b64Val.decode('utf-8')
    data = { "offset": 20 }
    headers = {
        'content-type': 'application/json',
        'Authorization': "Basic %s" %key_decoded
    }
    url = printful_api_base + "orders"

    response = requests.get(url, data, headers=headers)
    data = response.json()['result']
    print("response.json()['paging']['total']: ", response.json()['paging']['total'])
    print("response.json()['paging']['limit']: ", response.json()['paging']['limit'])
    print("response.json()['result']: ", response.json()['result'])
    return data

def create_printful_order(order, shipping_address):

# def create_printful_order(order):
    ''' This function submits a printful order '''
    # order_json = {
    #     "recipient": {
    #         "name": "Lester",
    #         "address1": "126 HH",
    #         "city": "New Canaan",
    #         "state_code": "CT",
    #         "country_code": "US",
    #         "zip": "06840"
    #     },
    #     "items": [{}]
    # }
    # order_json['retail_costs'] = { "shipping": "8.00" }
    # items = []
    # # Process each item in the order and attach them to the json object
    # # for order_item in order.items:
    # item = {
    #     "variant_id": "1962283513",
    #     "quantity": "1",
    #     "name": "Bubble-free stickers - 3x3",
    #     "retail_price": "25.00",
    #     "files": [{
    #         "id": "204393132"
    #     }]
    # }
    # items.append(item)
    # order_json['items'] = items

    order_json = {
        "recipient": {
            "name": shipping_address.customer.first_name + " " + shipping_address.customer.last_name,
            "address1": shipping_address.street_address,
            "city": shipping_address.city,
            "state_code": shipping_address.state,
            "country_code": shipping_address.country.code,
            "zip": shipping_address.zip
        },
        "items": [{
        #     "variant_id": 192,
        #     "quantity": 1,
        #     "name": "TaurusCanis Rex Logo T-Shirt - M",
        #     "retail_price": "25.00",
        #     "files": [{
        #         "id": 204371407,
        #         "url": "http://www.tauruscanisrex.com/static/images/website/TCR.png"
            # }]
        }]
    }

    for order_item in order.items.all():
        print("order_items: ", order_item.item)
        if order_item.item.item.category is not "T":
            print("order_items NOT Tip: ", order_item.item)
            new_order_item = {
                "variant_id": order_item.item.printful_variant_id,
                "quantity": order_item.quantity,
                "name": order_item.item.title,
                "retail_price": float(order_item.item.retail_price), #changed this on 8/22 is float ok compared to Decimal???
                "files": []
            }
            for file in order_item.item.itemvariantfiles_set.all():
                print("file_id: ", file.file_id)
                print("file_id: ", file.url)
                new_order_item['files'].append({
                    "id": file.file_id,
                    "url": file.url
                })
            order_json['items'].append(new_order_item)

    print("order_json: ", order_json)



    printful_api_base = 'https://api.printful.com/'
    key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
    b64Val = base64.b64encode(key_bytes)
    key_decoded = b64Val.decode('utf-8')
    headers = {
        'content-type': 'application/json',
        'Authorization': "Basic %s" %key_decoded
    }
    url = printful_api_base + "orders"

    try:
        response = requests.post(url, data=json.dumps(order_json),
                                 headers=headers)
        print("response = ", response.status_code, response.text)
        costs = requests.post(url + "/estimate-costs", data=json.dumps(order_json),
                                 headers=headers)
        print("costs = ", costs.status_code, costs.text)

        response_json = response.json()

        print("response.json: ", response_json['result']['retail_costs']['total'])
        print("order: ", order)

        order.printful_order_id = response_json['result']["id"]
        order.tax = response_json['result']['costs']['tax']
        order.shipping_cost = response_json['result']['retail_costs']['shipping']
        order.vat = response_json['result']['retail_costs']['vat']
        order.subtotal = response_json['result']['retail_costs']['subtotal']
        order.grand_total = response_json['result']['retail_costs']['total']
        order.save()
        return True, response
    except requests.exceptions.RequestException as e:
        print("ERROR: When submitting order with requests, "
              "error message: %s" % str(e))
        return False, e

def get_product_and_variants(product_id):
    printful_api_base = 'https://api.printful.com/'
    key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
    b64Val = base64.b64encode(key_bytes)
    key_decoded = b64Val.decode('utf-8')
    headers = {
        'content-type': 'application/json',
        'Authorization': "Basic %s" %key_decoded
    }
    url = printful_api_base + f"store/products/{product_id}"

    response = requests.get(url, headers=headers)
    data = response.json()['result']
    return data

class ProductsPage(ListView):
    # orders = get_orders()
    # # print("get_orders: ", orders)
    # order_ids = []
    # for order in orders:
    #     print("id: ", order['id'])
    #     delete_order(str(order['id']))
    model = Item
    paginate_by = 10
    template_name = "products_page.html"

    # def get(self, *args, **kwargs):
    #     product_details = get_product_and_variants(177576706)
    #     print("product_details: ", json.dumps(product_details))
    #     #get variants from printful
    #
    #     new_product = Item()
    #
    #     printful_sync_product_id = product_details['sync_product']['id']
    #     thumbnail_url = product_details['sync_product']['thumbnail_url']
    #     printful_name = product_details['sync_product']['name']
    #
    #     new_product.printful_product_id = printful_sync_product_id
    #     new_product.thumbnail_url = thumbnail_url
    #     new_product.image = thumbnail_url
    #     new_product.printful_name = printful_name
    #     new_product.save()
    #
    #     variants = [{}]
    #     for variant in product_details['sync_variants']:
    #         new_variant = ItemVariant()
    #         new_variant.item = new_product
    #
    #         printful_sync_variant_id = variant['variant_id']
    #         printful_price = variant['retail_price']
    #         variant_name = variant['name']
    #         sku = variant['sku']
    #         product_id = variant['product']['product_id']
    #
    #         new_variant.name = variant_name
    #         new_variant.printful_variant_id = printful_sync_variant_id
    #         new_variant.retail_price = printful_price
    #         new_variant.sku = sku
    #         new_variant.product_id = product_id
    #
    #         new_variant.save()
    #
    #         files = [{}]
    #         for file in variant['files']:
    #             new_variant_file = ItemVariantFiles()
    #             new_variant_file.item_variant = new_variant
    #
    #             file_id = file['id']
    #             file_url = file['url']
    #             filename = file['filename']
    #
    #             new_variant_file.file_id = file_id
    #             new_variant_file.url = file_url
    #             new_variant_file.file_name = filename
    #
    #             new_variant_file.save()
    #
    #             files.append({"file_id": file_id, "file_url": file_url, "filename": filename})
    #         variants.append({
    #             "printful_sync_product_id": printful_sync_product_id,
    #             "printful_sync_variant_id": printful_sync_variant_id,
    #             "printful_price": printful_price,
    #             "sku": sku,
    #             "product_id": product_id,
    #             "files": files})
    #
    #     print("variants: ", variants)
    #
    #     return render(self.request, "products_page.html")

        # create item_id

    # creating and order
        # products = get_products()
        # print("products: ", products)
        # print("orders: ", get_orders())
        # create_printful_order()
        # context = {
        #     'products': products
        # }
        # return render(self.request, "products_page.html", context)
    # creating and order



class HomeView(View):
    def get(self, *args, **kwargs):
        form = MailingListForm()
        context = {
            'form': form
        }
        # order = Order.objects.get(session_id=self.request.session['id'], ordered=False)
        # if order.billing_address:
        #     context = {
        #         'order': order,
        #         'DISPLAY_COUPON_FORM': False,
        #         'stripe_key': 'pk_test_4tNiwpsFHEX7N7hon7bpW4kE00saVfxboZ'
        #     }
        #     return render(self.request, "payment.html", context)
        # else:
        #     messages.warning(self.request, "You have not added a billing address")
        #     return redirect("core:checkout")

        # return HttpResponse("Homepage")
        return render(self.request, "home-page.html", context)
    def post(self, *args, **kwargs):
        form = MailingListForm(self.request.POST)
        print("form: ", form)
        if form.is_valid():
            try:
                print("valid")
                first_name = form.cleaned_data.get('first_name')
                print("first_name: ", first_name)
                email_address = form.cleaned_data.get('email_address')
                print("email_address: ", email_address)
                new_subscriber = MailingListSubscriber()
                new_subscriber.first_name=first_name
                new_subscriber.email_address=email_address
                new_subscriber.save()
                messages.success(self.request, "You have been added to the mailing list.")
                return redirect("/")
            except:
                messages.error(self.request, "There was an error. Please try again.")
                return redirect("/")
        else:
            messages.error(self.request, "There was an error. Please try again.")
            return redirect("/") 

# class OrderSummaryView(LoginRequiredMixin, View):
class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        print(self.request.session.keys())
        try:
            order = Order.objects.get(session_id = self.request.session['id'], ordered=False)
            context = {
                'object': order
            }
            print("order: ", order)
            for order_item in order.items.all():
                print("order_item: ", order_item)
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")

# class ItemDetailView(DetailView):
#     model = Item
#     template_name = "product-page.html"

#     def post(self, request, slug):
#         print("post_request: ", self.request.POST)
#         print("slug: ", slug)
#         print("quantity: ", self.request.POST.get('quantity'))
#         print("selected_variant_id: ", self.request.POST.get('selected_variant'))
#         print("printful_product_id: ", self.request.POST.get('printful_product_id'))
#         printful_product_id = self.request.POST.get('printful_product_id')
#         selected_variant_id = self.request.POST.get('selected_variant')
#         quantity = int(self.request.POST.get('quantity'))
#         # item_variant_id = int(self.request.POST.get('item_variant_id'))

#         print("QUANTITY: ", quantity)
#         quantity_count = quantity
#         print("Quantity Count: ", quantity_count)
#         for i in range(0, quantity):
#             add_to_cart(self.request, slug=None, item_variant_id=selected_variant_id, quantity=quantity_count, product_id=printful_product_id)
#             quantity_count -= 1
#         return redirect("core:order_summary")

class ItemDetailView(DetailView):
    # model = Item
    # template_name = "product-page.html"

    def get(self, request, slug):
        item = Item.objects.get(slug=slug)
        print("item: ", item)
        context = {
            "object": item
        }
        if item.category == "T":
            return render(self.request, "leave-a-tip.html", context)
        else:
            return render(self.request, "product-page.html", context)

    def post(self, request, slug):
        print("post_request: ", self.request.POST)
        print("slug: ", slug)
        print("quantity: ", self.request.POST.get('quantity'))
        print("selected_variant_id: ", self.request.POST.get('selected_variant'))
        print("printful_product_id: ", self.request.POST.get('printful_product_id'))

        if slug == "leave_a_tip":
            donation_amount = self.request.POST.get('donation_amount')
            add_donation_to_cart(self.request, slug=slug, donation_amount=donation_amount) 
        else:
            printful_product_id = self.request.POST.get('printful_product_id')
            selected_variant_id = self.request.POST.get('selected_variant')
            quantity = int(self.request.POST.get('quantity'))
            # item_variant_id = int(self.request.POST.get('item_variant_id'))
            
            print("QUANTITY: ", quantity)
            quantity_count = quantity
            print("Quantity Count: ", quantity_count)
            for i in range(0, quantity):
                add_to_cart(self.request, slug=None, item_variant_id=selected_variant_id, quantity=quantity_count, product_id=printful_product_id)
                quantity_count -= 1
        return redirect("core:order_summary")

def add_donation_to_cart(request, slug, donation_amount):
    item = get_object_or_404(ItemVariant, item__slug=slug)
    print("item: ", item)
    print("donation_amount: ", donation_amount)
    item.retail_price = donation_amount
    item.save()
    quantity = 1
    if 'id' not in request.session or request.session['id'] is None:
        request.session['id'] = create_session_id()
        request.session.modified = True
        print("request.session['id']: ", request.session['id'])
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        session_id = request.session['id'],
        ordered = False
    )
    print("order_item: ", order_item, " created: ", created)
    print("keys: ", request.session.keys())
    order_qs = Order.objects.filter(session_id = request.session['id'], ordered=False)
    print("order_qs: ", order_qs)
    if order_qs.exists():
        print("session keys: ", request.session.keys())
        print("order exists")
        order = order_qs[0]
        print("existing order: ", order)
        if order.items.filter(item__title = "Donation").exists():
            print("order_item if: ", order_item)
            order_item.quantity += 1
            order_item.save()
            print("ALPHA")
            if quantity == 1:
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order_summary")
            return
        else:
            print("order_item else: ", order_item)
            if quantity == 1:
                messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
            order.donation_added = True
            order.save()
            print("order: ", order)
            print("order_item: ", order_item)
            print("order_item: ", order_item.item.retail_price)
            print("order.items: ", order.items)
            # return redirect("core:order_summary")
            return
    else:
        print("order does not exist")
        ordered_date = timezone.now()
        order = Order.objects.create(session_id = request.session['id'], ordered_date=ordered_date)
        order.items.add(order_item)
        # request.session['id'] = create_session_id()
        # order.session_id = request.session['id']
        order.save()
        print("session keys: ", request.session.keys())
        if quantity == 1:
            messages.info(request, "This item was added to your cart.")
        # return redirect("core:order_summary")
        return
    return 

def tandc(request):
    return render(request, "tandc.html")

def pp(request):
    return render(request, "pp.html")

def returns_policy(request):
    return render(request, "returns.html")

# @login_required
def add_to_cart(request, slug=None, item_variant_id=None, quantity=1, product_id=None, variant_id=None, printful_product_id=None):
    # print("request.session['id']: ", request.session['id'])
    print("add to cart")
    if slug is None:
        print("product_id: ", product_id)
        print("variant_id: ", variant_id)
        print("printful_product_id: ", printful_product_id)
        print("slug none")
        print("quantity: ", quantity)

        print("ITEM_VARIANT_ID: ", item_variant_id)
        item =  get_object_or_404(ItemVariant, id=item_variant_id)
        print("ITEM: ", item)
        # else:
        # if product_id:
        #     item =  get_object_or_404(ItemVariant, item__printful_product_id=product_id, printful_variant_id=variant_id)
        # else:
        #     item = get_object_or_404(ItemVariant, item__printful_product_id=printful_product_id, printful_variant_id=variant_id)
        print("item: ", item)
        # print("request.user.id: ", request.user.id)
        print("session keys: ", request.session.keys())
        # print("request.session['id']: ", request.session['id'])
        # print("session id: ", request.session.id)
        # if 'id' not in request.session:
        #     request.session['id'] = create_session_id()
        if 'id' not in request.session or request.session['id'] is None:
            print("NOOONNNNNEEE")
            request.session['id'] = create_session_id()
            request.session.modified = True
            print("request.session['id']: ", request.session['id'])
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            session_id = request.session['id'],
            ordered = False
        )
        print("ORDER_ITEM*****: ", order_item, " CREATED: ", created)
        print("keys: ", request.session.keys())
        order_qs = Order.objects.filter(session_id = request.session['id'], ordered=False)
        if order_qs.exists():
            print("session keys: ", request.session.keys())
            print("order exists")
            order = order_qs[0]
            print("existing order: ", order)
            if order.items.filter(item__printful_variant_id = item.printful_variant_id).exists():
                print("order_item if: ", order_item)
                order_item.quantity += 1
                order_item.save()
                print("ALPHA")
                if quantity == 1:
                    messages.info(request, "This item quantity was updated.")
                    return redirect("core:order_summary")
                return
            else:
                print("order_item else: ", order_item)
                if quantity == 1:
                    messages.info(request, "This item was added to your cart.")
                order.items.add(order_item)
                order.save()
                print("order: ", order)
                print("order_item: ", order_item)
                print("order_item: ", order_item.item.retail_price)
                print("order.items: ", order.items)
                # return redirect("core:order_summary")
                return
        else:
            print("order does not exist")
            ordered_date = timezone.now()
            order = Order.objects.create(session_id = request.session['id'], ordered_date=ordered_date)
            print("ORDER_ITEM: ", order_item)
            order.items.add(order_item)
            print("order.items: ", order.items)
            # request.session['id'] = create_session_id()
            # order.session_id = request.session['id']
            order.save()
            print("session keys: ", request.session.keys())
            if quantity == 1:
                messages.info(request, "This item was added to your cart.")
            # return redirect("core:order_summary")
            return

    else:
        print("slug")
        item = get_object_or_404(Item, slug=slug)
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            user = request.user,
            ordered = False
        )
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__slug = item.slug).exists():
                order_item.quantity += 1
                order_item.save()
                print("BETA")
                messages.info(request, "This item quantity was updated.")
                # return redirect("core:order_summary")
                return
            else:
                messages.info(request, "This item was added to your cart.")
                order.items.add(order_item)
                # return redirect("core:order_summary")
                return
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            # return redirect("core:order_summary")
            return
    print("done")

# @login_required
def remove_from_cart(request, slug=None, item_variant_id=None):
    if slug is None:
        print("VARIANT_ID: ", item_variant_id)
        item = get_object_or_404(ItemVariant, id=item_variant_id)
        order_qs = Order.objects.filter(
            session_id=request.session['id'],
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__printful_variant_id = item.printful_variant_id).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    session_id = request.session['id'],
                    ordered = False
                )[0]
                order.items.remove(order_item)
                order_item.delete()
                messages.info(request, "This item was removed from your cart.")
                return redirect("core:order_summary")
            else:
                #add message saying order doesn't contain item
                messages.info(request, "This item was not in your cart.")
                return redirect("core:order_summary")
        else:
            #add message saying user doesn't have order
            messages.info(request, "You do not have an active order.")
            return redirect("core:order_summary")
    else:
        item = get_object_or_404(Item, slug=slug)
        order_qs = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__slug = item.slug).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    user = request.user,
                    ordered = False
                )[0]
                order.items.remove(order_item)
                order_item.delete()
                messages.info(request, "This item was removed from your cart.")
                return redirect("core:order_summary")
            else:
                #add message saying order doesn't contain item
                messages.info(request, "This item was not in your cart.")
                return redirect("core:product", slug = slug)
        else:
            #add message saying user doesn't have order
            messages.info(request, "You do not have an active order.")
            return redirect("core:product", slug = slug)

# @login_required
def remove_single_item_from_cart(request, slug=None, item_variant_id=None, printful_product_id=None):
    print("variant_id: ", item_variant_id)
    if slug is None:
        item = get_object_or_404(ItemVariant, id=item_variant_id)
        order_qs = Order.objects.filter(
            session_id=request.session['id'],
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__printful_variant_id = item.printful_variant_id).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    session_id = request.session['id'],
                    ordered = False
                )[0]
                if order_item.quantity > 1:
                    order_item.quantity -= 1
                else:
                    order.items.remove(order_item)
                order_item.save()
                print("GAMMA")
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order_summary")
            else:
                #add message saying order doesn't contain item
                messages.info(request, "This item was not in your cart.")
                return redirect("core:product", slug = slug)
        else:
            #add message saying user doesn't have order
            messages.info(request, "You do not have an active order.")
            return redirect("core:product", slug = slug)

    else:
        item = get_object_or_404(Item, slug=slug)
        order_qs = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__slug = item.slug).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    user = request.user,
                    ordered = False
                )[0]
                if order_item.quantity > 1:
                    order_item.quantity -= 1
                else:
                    order.items.remove(order_item)
                order_item.save()
                print("DELTA")
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order_summary")
            else:
                #add message saying order doesn't contain item
                messages.info(request, "This item was not in your cart.")
                return redirect("core:product", slug = slug)
        else:
            #add message saying user doesn't have order
            messages.info(request, "You do not have an active order.")
            return redirect("core:product", slug = slug)

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist.")
        return redirect("core:checkout")

class AddCoupon(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully applied coupon.")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order.")
                return redirect("core:checkout")

class RequestRefund(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)
    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request_refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request_refund")

from django.shortcuts import render
from cart.cart import Cart
from payment.models import ShippingAddress
from payment.forms import ShippingForm, PaymentForm
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def checkout(request):
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    total = cart.cart_total
    shipping_address = ShippingAddress.objects.get(user__id=request.user.id)
    # shipping_form = ShippingForm(request.POST or None, instance=shipping_address)
    context = {'cart_products':cart_products, 'quantities':quantities, 'total':total, 'shipping_address':shipping_address}
    return render(request, 'payment/checkout.html', context=context)


@login_required(login_url='login')
def billing_info(request):
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    total = cart.cart_total
    shipping_address = ShippingAddress.objects.get(user__id=request.user.id)
    billing_form = PaymentForm()
    context = {'cart_products':cart_products, 'quantities':quantities, 'total':total, 'shipping_address':shipping_address, 'billing_form':billing_form}
    return render(request, 'payment/billing_info.html', context=context)



def payment_success(request):
    context = {}
    return render(request, 'payment/payment_success.html', context=context)
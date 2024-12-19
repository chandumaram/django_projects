from django.shortcuts import redirect, render, get_object_or_404
from .cart import Cart
from store.models import Product
from django.http import JsonResponse
from django.contrib import messages

# Create your views here.
def cart_summary(request):
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    total = cart.cart_total
    context = {'cart_products':cart_products, 'quantities':quantities, 'total':total}
    return render(request, 'cart/cart_summary.html', context=context)

def cart_add(request):
    # Get the cart
    cart = Cart(request)
    # test for POST
    if request.POST.get('action') == 'post':
        # get stuff
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        # lookup product in DB
        product = get_object_or_404(Product, id=product_id)
        # Save to session
        cart.add(productId=product.id, quantity=product_qty)
        # get cart quantity
        cart_quanity = cart.__len__()
        # return response
        response = JsonResponse({'qty':cart_quanity})
        messages.success(request, "Product added to cart...")
        return response

def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        cart.update(productId=product_id, quantity=product_qty)
        response = JsonResponse({'qty':product_qty})
        messages.success(request, "Your cart has been updated...")
        return response

def crat_delete(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        cart.delete(productId=product_id)
        response = JsonResponse({'product':product_id})
        messages.success(request, "Product removed from cart...")
        return response


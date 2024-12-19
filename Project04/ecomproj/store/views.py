from django.shortcuts import render, redirect
# from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, Profile
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
import json
from cart.cart import Cart
from payment.models import ShippingAddress
from payment.forms import ShippingForm

# Create your views here.
def home(request):
    # products = Product.objects.all()
    # context = {'products':products}
    # return render(request, 'store/home.html', context=context)
    query = request.GET.get('q', '')  # Get search query if available
    # products = Product.objects.all()  # Start with all products
    # print(products)
    # If there's a search query, filter the products
    if query:
        # categories =Category.objects.filter(Q(name__icontains=query))
        # products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
        products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
    else:
        products = Product.objects.all()
    # # Pagination
    # paginator = Paginator(products, 10)  # Show 10 products per page
    # page_number = request.GET.get('page')
    # products_page = paginator.get_page(page_number)
    
    # context = {'products':products_page, 'query': query,}
    context = {'products':products}
    return render(request, 'store/home.html', context=context)

def about(request):
    context = {}
    return render(request, 'store/about.html', context=context)

def product(request, pk):
    product = Product.objects.get(id=pk)
    context = {'product':product}
    return render(request, 'store/product.html', context=context)

def category(request, slug):
    # replace hyphens with space
    # foo = foo.replace('-', ' ')
    try:
        category = Category.objects.get(slug=slug)
        products = Product.objects.filter(category=category)
        return render(request, 'store/category.html', {'category':category, 'products':products})
    except:
        messages.success(request, "That category doesn't exist..."+slug)
        return redirect('home')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            # log in user
            user = authenticate(request, username=username, password=password)
            login(request, user)
            messages.success(request, "You have been logged in!")
            return redirect('home')
        else:
            messages.success(request, "Oops! There was a problem Registering, please try again...")
            return redirect('register')
    else:
        context = {'form':form}
        return render(request, 'store/register.html', context=context)

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # do some shopping cart stuff
            current_user = Profile.objects.get(user__id=request.user.id)
            # get their saved cart from database
            saved_cart = current_user.old_cart
            # convert database string into python dictionary
            if saved_cart:
                converted_cart = json.loads(saved_cart)
                # add the loaded cart dictionary to our session
                # get the cart
                cart = Cart(request)
                # loop the database cart items and add to session cart
                for key, value in converted_cart.items():
                    cart.add(productId=key, quantity=value)

            messages.success(request, "You have been logged in!")
            return redirect('home')
        else:
            messages.success(request, "Something went wrong, please try again...")
            return redirect('login')
    else:
        context = {}
        return render(request, 'store/login.html', context=context)

# @login_required(login_url='login')
def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        form = UpdateUserForm(request.POST or None, instance=current_user)
        if form.is_valid():
            form.save()
            login(request, current_user)
            messages.success(request, "User has been updated!!")
            return redirect('home')
        context = {'form':form}
        return render(request, 'store/update_user.html', context=context)
    else:
        messages.success(request, "You must be logged in to access profile page!!")
        return redirect('home')
    
def update_info(request):
    if request.user.is_authenticated:
        current_user = Profile.objects.get(user__id=request.user.id)
        shipping_address = ShippingAddress.objects.get(user__id=request.user.id)

        form = UserInfoForm(request.POST or None, instance=current_user)
        shipping_form = ShippingForm(request.POST or None, instance=shipping_address)
        if form.is_valid() and shipping_form.is_valid():
            form.save()
            shipping_form.save()
            messages.success(request, "Your info has been updated!!")
            return redirect('home')
        context = {'form':form, 'shipping_form':shipping_form}
        return render(request, 'store/update_info.html', context=context)
    else:
        messages.success(request, "You must be logged in to access profile page!!")
        return redirect('home')
    
def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        print(current_user)
        # did they fill out the form
        if request.method == 'POST':
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password changed successfully, please login again..")
                # login(request, current_user)
                return redirect('login')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect('update_password')
        else:
            form = ChangePasswordForm(current_user)
            context = {'form':form}
            return render(request, 'store/update_password.html', context=context)
    else:
        messages.success(request, "You must be logged in to access update password page!!")
        return redirect('home')

def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out...")
    return redirect('home')
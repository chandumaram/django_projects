from django.shortcuts import render, redirect
from .forms import CreateUserForm, LoginForm, CreateRecordForm, UpdateRecordForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required 
from django.contrib import messages

from .models import Record

# Home Page
def home(request):
    return render(request, 'webapp/index.html')


# Register a User
def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect("login")
    context = {'form':form}
    return render(request, 'webapp/register.html', context=context)

# User Login
def user_login(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            return redirect("dashboard")
    context = {'form':form}
    return render(request, 'webapp/login.html', context=context)

# Dashboard
@login_required(login_url="login")
def dashboard(request):
    my_records = Record.objects.all()
    context = {'records': my_records}
    return render(request, 'webapp/dashboard.html', context=context)

# Create record
@login_required(login_url="login")
def create_record(request):
    form = CreateRecordForm()
    if request.method == "POST":
        form = CreateRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Record created successfully.")
            return redirect("dashboard")
    context = {'form': form}
    return render(request, 'webapp/create-record.html', context=context)

# Update record
@login_required(login_url="login")
def update_record(request, pk):
    record = Record.objects.get(id=pk)
    form = UpdateRecordForm(instance=record)
    if request.method == "POST":
        form = UpdateRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Record updated successfully.")
            return redirect("dashboard")
    context = {'form': form}
    return render(request, 'webapp/update-record.html', context=context)

# View record
@login_required(login_url="login")
def view_record(request, pk):
    record = Record.objects.get(id=pk)
    context = {'record': record}
    return render(request, 'webapp/view-record.html', context=context)

# Delete record
@login_required(login_url="login")
def delete_record(request, pk):
    record = Record.objects.get(id=pk)
    record.delete()
    messages.success(request, "Record deleted successfully.")
    return redirect("dashboard")

# Logout User
def user_logout(request):
    logout(request)
    messages.success(request, "You logged out successfully.")
    return redirect("login")
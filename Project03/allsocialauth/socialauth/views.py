from django.shortcuts import render

# Create your views here.
def homepage(request):
    return render(request, 'socialauth/index.html')

def dashboard(request):
    return render(request, 'socialauth/dashboard.html')
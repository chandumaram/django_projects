from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name=""),
    path('dashboard', views.dashboard, name="dashboard")
]

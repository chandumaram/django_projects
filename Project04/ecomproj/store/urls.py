from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('about/', views.about, name="about"),
    path('register/', views.register_user, name="register"),
    path('login/', views.login_user, name="login"),
    path('update_user/', views.update_user, name="update_user"),
    path('update_info/', views.update_info, name="update_info"),
    path('update_password/', views.update_password, name="update_password"),
    path('logout/', views.logout_user, name="logout"),
    path('product/<int:pk>', views.product, name="product"),
    path('category/<str:slug>', views.category, name="category"),
]

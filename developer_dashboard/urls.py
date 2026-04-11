from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='dev_login'),
    path('logout/', views.logout_view, name='dev_logout'),
]

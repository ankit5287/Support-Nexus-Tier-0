from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('logic-lab/', views.logic_lab, name='logic_lab'),
    path('login/', views.login_view, name='dev_login'),
    path('signup/', views.signup_view, name='dev_signup'),
    path('logout/', views.logout_view, name='dev_logout'),
    path('ide/', views.ide_view, name='ide_view'),
]

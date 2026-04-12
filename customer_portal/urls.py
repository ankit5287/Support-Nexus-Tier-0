from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('support/', RedirectView.as_view(url='/', permanent=True)),
    path('home/', views.landing, name='landing'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('login/', views.login_view, name='dev_login'),
    path('signup/', views.signup_view, name='dev_signup'),
    path('logout/', views.logout_view, name='dev_logout'),
    path('ide/', views.ide_view, name='ide_view'),
    path('team/<str:team_name>/', views.team_view, name='team_view'),
    path('transfer/<int:ticket_id>/', views.transfer_ticket, name='transfer_ticket'),
    path('update-status-htmx/<int:ticket_id>/', views.update_status_htmx, name='update_status_htmx'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
]

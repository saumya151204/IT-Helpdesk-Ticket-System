from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

   
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('create/', views.create_ticket, name='create_ticket'),
    path('update/<int:id>/', views.update_ticket, name='update_ticket'),
    path('ticket/<int:id>/', views.ticket_detail, name='ticket_detail'),
]
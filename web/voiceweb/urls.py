from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.admin_login_view, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('unlock/', views.unlock_page, name='unlock_page'),  
    path('logout/', views.logout, name='logout'),
    path('enroll/', views.enroll, name='enroll'),
    path('unlock-api/', views.unlock, name='unlock'), 
    path('logs/', views.logs, name='logs'),
]
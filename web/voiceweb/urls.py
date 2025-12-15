from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.admin_login_view, name='admin_login'),
    path('panel/', views.admin_panel, name='admin_panel'),
    path('enroll/', views.enroll, name='enroll'),
    path('unlock/', views.unlock, name='unlock'),
    path('logs/', views.logs, name='logs'),
]
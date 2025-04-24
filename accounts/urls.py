# skampus/urls.py

from django.contrib import admin
from django.urls import path
from accounts import views  # views dosyasını import ediyoruz

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),  # Giriş sayfasını anasayfa olarak ayarlıyoruz
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),  # Kayıt ol sayfası
]

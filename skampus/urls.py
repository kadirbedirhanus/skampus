from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as account_views

urlpatterns = [
    # Yönetim panelleri
    path('admin/', admin.site.urls),

    # Kullanıcı işlemleri
    path('', account_views.login_view, name='login'),
    path('register/', account_views.register_view, name='register'),
    path('logout/', account_views.logout_view, name='logout'),

    # Uygulama içeriği
    path('home/', account_views.home_view, name='home'),
    path('goal/<int:goal_id>/', account_views.goal_detail, name='goal_detail'),
    path('goal/<int:goal_id>/subgoals/', account_views.subgoal_list_view, name='subgoal_list'),
    path('subgoal/<int:subgoal_id>/save_rating/', account_views.save_subgoal_rating, name='save_subgoal_rating'),
]

# Geliştirme ortamında statik dosyalar
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

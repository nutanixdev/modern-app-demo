from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('watchlist.urls')),
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

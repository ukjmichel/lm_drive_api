# lm_drive_api/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("authentication.urls")),
    path("api/", include("store.urls")),
    path("api/orders/", include("orders.urls")),  # Include orders app URLs
]

# payments/urls.py
from django.urls import path
from .views import CreatePaymentIntentView, UpdatePaymentStatusView

urlpatterns = [
    path(
        "create-payment-intent/<str:order_id>/",
        CreatePaymentIntentView.as_view(),
        name="create-payment-intent",
    ),
    path(
        "update-payment-status/",
        UpdatePaymentStatusView.as_view(),
        name="update-payment-status",
    ),
]

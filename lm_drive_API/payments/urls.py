from django.urls import path
from .views import (
    CreatePaymentIntentView,
)  # Adjust the import based on your project structure

urlpatterns = [
    path(
        "create-payment-intent/<str:order_id>/",
        CreatePaymentIntentView.as_view(),
        name="create-payment-intent",
    )
]

from django.urls import path
from .views import process_payment  # Adjust the import based on your project structure

urlpatterns = [
    path("process/", process_payment, name="process_payment"),
]

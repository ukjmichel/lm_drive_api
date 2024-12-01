import random
from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction


def generate_unique_customer_id():
    """Génère un identifiant client unique de 10 chiffres."""
    while True:
        customer_id = "".join([str(random.randint(0, 9)) for _ in range(10)])
        if not Customer.objects.filter(customer_id=customer_id).exists():
            return customer_id


class Customer(models.Model):
    customer_id = models.CharField(
        max_length=10, unique=True, default=generate_unique_customer_id
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,  # Permet les valeurs nulles pour les clients non créés dans Stripe
    )
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    email = models.EmailField(unique=True)  # Garantit l'unicité de l'email

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.customer_id})"

    def clean(self):
        """Validation personnalisée pour les champs ID client et email."""
        # Validation de l'email
        if not self.email:
            raise ValidationError({"email": "L'adresse e-mail ne peut pas être vide."})

        # Validation de la longueur du nom d'utilisateur
        username = self.user.username
        if len(username) < 4:
            raise ValidationError(
                {"user": "Le nom d'utilisateur doit contenir au moins 4 caractères."}
            )
        if len(username) > 20:
            raise ValidationError(
                {"user": "Le nom d'utilisateur ne peut pas dépasser 20 caractères."}
            )

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour garantir l'unicité et exécuter la validation."""
        self.full_clean()  # Appelle automatiquement la méthode clean()
        super().save(*args, **kwargs)

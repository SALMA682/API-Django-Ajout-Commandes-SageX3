from django.db import models
from django.contrib.auth.models import User

class Commande(models.Model):
    STATUT_CHOICES = [
        ('non_validee', 'Non validée'),
        ('validee', 'Validée'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data_formulaire = models.JSONField()  # Contenu du formulaire
    client_sage = models.JSONField(null=True, blank=True)
    articles_sage = models.JSONField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='non_validee')
    id_sage = models.CharField(max_length=50, null=True, blank=True) 
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande {self.id} - {self.statut}"

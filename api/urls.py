from django.urls import path
from .views import get_clients,get_articles,save_commande,commandes_non_validees,commandes_validees,valider_commande,get_article_details,get_client_details,get_sites,get_article_stock
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # endpoint pour obtenir token (login)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # endpoint pour rafraîchir token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('clients/', get_clients, name='get_clients'),
    path('articles/', get_articles, name='get_articles'),
    path('sites/', get_sites, name='get_sites'),
    path('stock/', get_article_stock, name='get_artisle_stock'),
    path('clientsDetails/<str:code_client>/', get_client_details, name='get_clients_details'),
    path('articlesDetails/<str:code_article>/', get_article_details, name='get_articles_details'),
    path('save_commande/', save_commande, name='save_commande'),
    path('commandes/non_validees/', commandes_non_validees, name='commandes_non_validees'),
    path('commandes/validees/', commandes_validees, name='commandes_validees'),
    path('valider_commande/', valider_commande, name='valider_commande'),
]


from django.urls import path

from .views import create_reservation, list_slots_available


urlpatterns = [
    path("reservas/", create_reservation, name="criar-reserva"),
    path("reservas/listar/", list_slots_available, name="listar-slots-disponiveis"),
]

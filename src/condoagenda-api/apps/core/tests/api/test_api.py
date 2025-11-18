from datetime import date, time
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.models import Apartamento, Configuracao


class ReservaAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.apartamento = Apartamento.objects.create(numero=101, responsavel="João")
        self.config = Configuracao.objects.create(
            hora_inicio=time(7, 0),
            hora_fim=time(19, 0),
            duracao_reserva_minutos=120,
            quantidade_agendamento_por_apartamento=2,
        )

    def test_create_reservation_success(self):
        today = date.today()

        data = {
            "data": str(today),
            "hora": "09:00:00",
            "apartamento": self.apartamento.id,
            "andar": 0,
        }

        response = self.client.post("/api/reservas/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("hora_saida", response.data)
        self.assertEqual(response.data["hora_saida"], "11:00:00")

    def test_create_reservation_with_even_hour_fails(self):
        today = date.today()

        data = {
            "data": str(today),
            "hora": "08:00:00",
            "apartamento": self.apartamento.id,
            "andar": 0,
        }

        response = self.client.post("/api/reservas/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("hora", response.data)

from datetime import date, time
from django.test import TestCase
from apps.core.models import Apartamento, Configuracao
from apps.core.api.serializers import ReservaSerializer


class ReservaSerializerTestCase(TestCase):
    
    def setUp(self):
        self.apartamento = Apartamento.objects.create(numero=101, responsavel="João")
        self.config = Configuracao.objects.create(
            hora_inicio=time(7, 0),
            hora_fim=time(19, 0),
            duracao_reserva_minutos=120,
            quantidade_agendamento_por_apartamento=2
        )
    
    def test_create_reserva_with_hora_saida_calculated(self):
        today = date.today()
        
        data = {
            "data": today,
            "hora": time(9, 0),
            "apartamento": self.apartamento.id,
            "andar": 0
        }
        
        serializer = ReservaSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        reserva = serializer.save()
        
        self.assertIsNotNone(reserva.hora_saida)
        self.assertEqual(reserva.hora, time(9, 0))
        self.assertEqual(reserva.hora_saida, time(11, 0))
    
    def test_serializer_returns_hora_saida_in_response(self):
        today = date.today()
        
        data = {
            "data": today,
            "hora": time(9, 0),
            "apartamento": self.apartamento.id,
            "andar": 0
        }
        
        serializer = ReservaSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        reserva = serializer.save()
        
        response_serializer = ReservaSerializer(reserva)
        response_data = response_serializer.data
        
        self.assertIn("hora_saida", response_data)
        self.assertEqual(response_data["hora_saida"], "11:00:00")
    
    def test_serializer_validates_business_rules(self):
        today = date.today()
        
        data = {
            "data": today,
            "hora": time(8, 0),
            "apartamento": self.apartamento.id,
            "andar": 0
        }
        
        serializer = ReservaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("hora", serializer.errors)


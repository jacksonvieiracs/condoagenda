from datetime import date, time, timedelta
from django.test import TestCase
from apps.core.models import Apartamento, Configuracao, Reserva
from apps.core.services import ReservaService, ReservaValidationError


class ReservaServiceTestCase(TestCase):
    
    def setUp(self):
        self.apartamento = Apartamento.objects.create(numero=101, responsavel="João")
        self.config = Configuracao.objects.create(
            hora_inicio=time(7, 0),
            hora_fim=time(19, 0),
            duracao_reserva_minutos=120,
            quantidade_agendamento_por_apartamento=2
        )
    
    def test_get_current_week_range(self):
        start, end = ReservaService.get_current_week_range()
        self.assertEqual((end - start).days, 6)
        self.assertEqual(start.weekday(), 0)
        self.assertEqual(end.weekday(), 6)
    
    def test_is_odd_hour(self):
        self.assertTrue(ReservaService.is_odd_hour(time(7, 0)))
        self.assertTrue(ReservaService.is_odd_hour(time(9, 0)))
        self.assertTrue(ReservaService.is_odd_hour(time(11, 0)))
        self.assertFalse(ReservaService.is_odd_hour(time(8, 0)))
        self.assertFalse(ReservaService.is_odd_hour(time(10, 0)))
    
    def test_cannot_book_outside_current_week(self):
        next_week_date = date.today() + timedelta(days=8)
        
        with self.assertRaises(ReservaValidationError) as context:
            ReservaService.validate_reserva(
                next_week_date,
                time(9, 0),
                self.apartamento,
                0
            )
        
        self.assertIn("semana atual", context.exception.message)
    
    def test_cannot_book_past_dates(self):
        past_date = date.today() - timedelta(days=1)
        
        with self.assertRaises(ReservaValidationError) as context:
            ReservaService.validate_reserva(
                past_date,
                time(9, 0),
                self.apartamento,
                0
            )
        
        self.assertIn("semana atual", context.exception.message.lower())
    
    def test_cannot_book_even_hours(self):
        today = date.today()
        
        with self.assertRaises(ReservaValidationError) as context:
            ReservaService.validate_reserva(
                today,
                time(8, 0),
                self.apartamento,
                0
            )
        
        self.assertIn("ímpares", context.exception.message)
    
    def test_cannot_book_duplicate_slot(self):
        today = date.today()
        
        Reserva.objects.create(
            data=today,
            hora=time(9, 0),
            apartamento=self.apartamento,
            andar=0
        )
        
        apartamento2 = Apartamento.objects.create(numero=102, responsavel="Maria")
        
        with self.assertRaises(ReservaValidationError) as context:
            ReservaService.validate_reserva(
                today,
                time(9, 0),
                apartamento2,
                0
            )
        
        self.assertIn("Já existe uma reserva", context.exception.message)
    
    def test_cannot_exceed_max_reservations_per_day(self):
        today = date.today()
        
        Reserva.objects.create(
            data=today,
            hora=time(9, 0),
            apartamento=self.apartamento,
            andar=0
        )
        
        Reserva.objects.create(
            data=today,
            hora=time(11, 0),
            apartamento=self.apartamento,
            andar=1
        )
        
        with self.assertRaises(ReservaValidationError) as context:
            ReservaService.validate_reserva(
                today,
                time(13, 0),
                self.apartamento,
                0
            )
        
        self.assertIn("limite", context.exception.message)
    
    def test_successful_reservation_creation(self):
        today = date.today()
        
        reserva = ReservaService.create_reserva(
            today,
            time(9, 0),
            self.apartamento,
            0
        )
        
        self.assertIsNotNone(reserva.id)
        self.assertEqual(reserva.data, today)
        self.assertEqual(reserva.hora, time(9, 0))
        self.assertEqual(reserva.apartamento, self.apartamento)
    
    def test_can_book_different_floors_same_time(self):
        today = date.today()
        apartamento2 = Apartamento.objects.create(numero=102, responsavel="Maria")
        
        reserva1 = ReservaService.create_reserva(
            today,
            time(9, 0),
            self.apartamento,
            0
        )
        
        reserva2 = ReservaService.create_reserva(
            today,
            time(9, 0),
            apartamento2,
            1
        )
        
        self.assertIsNotNone(reserva1.id)
        self.assertIsNotNone(reserva2.id)


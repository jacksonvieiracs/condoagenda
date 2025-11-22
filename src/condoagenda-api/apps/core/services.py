from datetime import date, datetime, timedelta
from typing import Tuple

from apps.core.models import Apartamento, Configuracao, Reserva


class ReservaValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ReservaService:
    @staticmethod
    def get_current_week_range() -> Tuple[date, date]:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week

    @staticmethod
    def is_odd_hour(hora: datetime.time) -> bool:
        return hora.hour % 2 != 0

    @staticmethod
    def validate_reserva(data: date, hora: datetime.time, numero_apartamento: int, andar: int):
        config, _ = Configuracao.objects.get_or_create(id=1)

        start_of_week, end_of_week = ReservaService.get_current_week_range()
        if data < start_of_week or data > end_of_week:
            raise ReservaValidationError(
                "Só é possível reservar slots dentro da semana atual (segunda a domingo).",
                field="data",
            )

        if data < date.today():
            raise ReservaValidationError(
                "Não é possível reservar slots em datas passadas.", field="data"
            )

        if not ReservaService.is_odd_hour(hora):
            raise ReservaValidationError(
                "Só é possível agendar em horários ímpares (07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00).",
                field="hora",
            )

        if Reserva.objects.filter(data=data, hora=hora, andar=andar).exists():
            raise ReservaValidationError(
                "Já existe uma reserva para este horário e andar.", field="hora"
            )

        reservas_apartamento_no_dia = Reserva.objects.filter(
            data=data, apartamento__numero=numero_apartamento
        ).count()

        max_por_apartamento = config.quantidade_agendamento_por_apartamento
        if reservas_apartamento_no_dia >= max_por_apartamento:
            raise ReservaValidationError(
                f"O apartamento já atingiu o limite de {max_por_apartamento} reservas para este dia.",
                field="apartamento",
            )

        if hora < config.hora_inicio or hora > config.hora_fim:
            raise ReservaValidationError(
                f"O horário deve estar entre {config.hora_inicio.strftime('%H:%M')} e {config.hora_fim.strftime('%H:%M')}.",
                field="hora",
            )

    @staticmethod
    def create_reserva(
        data: date,
        hora: datetime.time,
        numero_apartamento,
        andar: int,
    ) -> Reserva:
        config, _ = Configuracao.objects.get_or_create(id=1)
        apartamento = Apartamento.objects.get(numero=numero_apartamento)

        hora_datetime = datetime.combine(data, hora)
        hora_saida_datetime = hora_datetime + timedelta(
            minutes=config.duracao_reserva_minutos
        )
        hora_saida = hora_saida_datetime.time()

        reserva = Reserva.objects.create(
            data=data,
            hora=hora,
            apartamento=apartamento,
            andar=andar,
            hora_saida=hora_saida,
        )

        return reserva

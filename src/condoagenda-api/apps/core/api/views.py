from datetime import date, datetime, timedelta

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.core.models import Configuracao, Reserva
from apps.core.services import ReservaService

from django.utils import timezone

from .serializers import (
    CriarReservaRequestSerializer,
    ListarDatasDisponiveisRequestSerializer,
    ListarDatasDisponiveisResponseSerializer,
    ListarSlotsDisponiveisRequestSerializer,
    ListarSlotsDisponiveisResponseSerializer,
    ListarMinhasReservasResponseSerializer,
)


def get_slots(dia: date, andar: int):
    configuracao, _ = Configuracao.objects.get_or_create(id=1)
    inicio = datetime.combine(dia, configuracao.hora_inicio)
    fim = datetime.combine(dia, configuracao.hora_fim)
    delta = timedelta(minutes=configuracao.duracao_reserva_minutos)

    # start_of_week, end_of_week = ReservaService.get_current_week_range()
    # is_out_of_week = dia < start_of_week or dia > end_of_week
    reservas = Reserva.objects.filter(data=dia, andar=andar)
    horarios_reservados = set(reservas.values_list("hora", flat=True))

    agora = datetime.now()
    is_passed = dia < agora.date()

    slots = []
    atual = inicio
    while atual + delta <= fim + delta:
        inicio_slot = atual.time()
        fim_slot = (atual + delta).time()

        is_odd_hour = ReservaService.is_odd_hour(inicio_slot)
        is_reserved = inicio_slot in horarios_reservados
        # is_available = (
        #     is_odd_hour and not is_reserved and not is_passed and not is_out_of_week
        # )
        is_available = is_odd_hour and not is_reserved and not is_passed

        slots.append(
            {
                "start": inicio_slot.strftime("%H:%M"),
                "end": fim_slot.strftime("%H:%M"),
                "available": is_available,
            }
        )
        atual += delta

    return slots


def get_dates(andar: int):
    today = timezone.now().date()
    current_weekday = today.weekday()
    start_of_week = today - timedelta(days=current_weekday)
    dates = [start_of_week + timedelta(days=i) for i in range(7)]

    datas = []
    for cdate in dates:
        slots = get_slots(cdate, andar)
        quantidade_slots_disponiveis = len(
            [slot for slot in slots if slot["available"]]
        )

        datas.append(
            {
                "data": cdate,
                "quantidade_slots_disponiveis": quantidade_slots_disponiveis,
                "disponivel": quantidade_slots_disponiveis > 0,
            }
        )

    return datas


@api_view(["POST"])
def create_reservation(request):
    serializer = CriarReservaRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(status=status.HTTP_201_CREATED)


@api_view(["GET"])
def list_slots_available(request):
    serializer = ListarSlotsDisponiveisRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    dia = data["data"]
    andar = data["andar"]

    slots = get_slots(dia, andar)
    return Response(
        ListarSlotsDisponiveisResponseSerializer(
            {"slots": slots, "data": dia, "andar": andar}
        ).data,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def list_dates_available(request):
    serializer = ListarDatasDisponiveisRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    andar = data["andar"]

    datas = get_dates(andar)
    return Response(
        ListarDatasDisponiveisResponseSerializer({"datas": datas}).data,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def my_reservations(request):
    numero_apartamento = request.query_params.get("numero_apartamento")
    if not numero_apartamento:
        return Response(
            {"error": "Número do apartamento é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reservations = Reserva.objects.filter(apartamento__numero=int(numero_apartamento))

    return Response(
        ListarMinhasReservasResponseSerializer({"reservas": reservations}).data,
        status=status.HTTP_200_OK,
    )

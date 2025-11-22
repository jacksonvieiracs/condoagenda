from dataclasses import Field
import logging
from datetime import date, time
from typing import Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Reservation(BaseModel):
    data: date
    hora: time
    apartamento: int
    andar: int


class Slot(BaseModel):
    start: time
    end: time
    available: bool

    def __str__(self) -> str:
        return f"{self.start:%H:%M} as {self.end:%H:%M}"

class DataDisponivel(BaseModel):
    data: date
    quantidade_slots_disponiveis: int
    disponivel: bool

class ListarDatasDisponiveisResponse(BaseModel):
    datas: list[DataDisponivel]
    error: Optional[str] = None

class ListarHorariosResponse(BaseModel):
    slots: list[Slot]
    error: Optional[str] = None


class CriarReservaResponse(BaseModel):
    is_success: bool
    message: str | None = None

class MinhaReserva(BaseModel):
    data: date
    hora: time
    hora_saida: time

class MinhasReservasResponse(BaseModel):
    reservas: list[MinhaReserva]
    error: Optional[str] = None


def format_date_to_api(date: date) -> str:
    return date.strftime("%Y-%m-%d")


def format_time_to_api(time: time) -> str:
    return time.strftime("%H:%M")


class CondoAgendaApiService:
    BASE_URL = "http://localhost:8000/api"
    TIMEOUT_IN_SECONDS = 10

    @staticmethod
    async def listar_horarios_disponiveis(
        date: date, andar: int
    ) -> ListarHorariosResponse:
        try:
            async with httpx.AsyncClient(
                timeout=CondoAgendaApiService.TIMEOUT_IN_SECONDS
            ) as client:
                response = await client.get(
                    f"{CondoAgendaApiService.BASE_URL}/reservas/listar/",
                    params={"data": format_date_to_api(date), "andar": andar},
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Horários disponíveis: {data}")
                return ListarHorariosResponse(**data)

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao buscar horários: {str(e)}")
            return ListarHorariosResponse(
                slots=[], error="Erro ao buscar horários"
            )

        except Exception as e:
            logger.error(f"Erro inesperado ao buscar horários: {str(e)}")
            return ListarHorariosResponse(
                slots=[], error="Erro inesperado ao buscar horários"
            )

    @staticmethod
    async def listar_datas_disponiveis(andar: int) -> ListarDatasDisponiveisResponse:
        try:
            async with httpx.AsyncClient(
                timeout=CondoAgendaApiService.TIMEOUT_IN_SECONDS
            ) as client:
                response = await client.get(
                    f"{CondoAgendaApiService.BASE_URL}/reservas/listar/datas/",
                    params={"andar": andar},
                )
                response.raise_for_status()
                data = response.json()
                datas = data["datas"]
                logger.info(f"Datas disponíveis: {datas}")
                return ListarDatasDisponiveisResponse(datas=[DataDisponivel(**data) for data in datas])
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao buscar datas disponíveis: {str(e)}")
            return ListarDatasDisponiveisResponse(datas=[], error="Erro ao buscar datas disponíveis")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar datas disponíveis: {str(e)}")
            return ListarDatasDisponiveisResponse(datas=[], error="Erro inesperado ao buscar datas disponíveis")

    @staticmethod
    async def criar_reserva(reservation: Reservation) -> CriarReservaResponse:
        try:
            payload = {
                "data": format_date_to_api(reservation.data),
                "hora": format_time_to_api(reservation.hora),
                "numero_apartamento": reservation.apartamento,
                "andar": reservation.andar,
            }

            async with httpx.AsyncClient(
                timeout=CondoAgendaApiService.TIMEOUT_IN_SECONDS
            ) as client:
                response = await client.post(
                    f"{CondoAgendaApiService.BASE_URL}/reservas/",
                    json=payload,
                )

                response.raise_for_status()
                return CriarReservaResponse(
                    is_success=True, message="Reserva criada com sucesso"
                )

        except httpx.HTTPStatusError as e:
            print(e.response.json())
            logger.error(f"Erro ao criar reserva: {str(e)}")
            return CriarReservaResponse(is_success=False, message=str(e))

        except Exception as e:
            logger.error(f"Erro inesperado ao criar reserva: {str(e)}")
            return CriarReservaResponse(
                is_success=False, message="Erro inesperado ao criar reserva"
            )

    @staticmethod
    async def listar_minhas_reservas(numero_apartamento: int) -> MinhasReservasResponse:
        try:
            async with httpx.AsyncClient(
                timeout=CondoAgendaApiService.TIMEOUT_IN_SECONDS
            ) as client:
                response = await client.get(
                    f"{CondoAgendaApiService.BASE_URL}/reservas/listar/minhas-reservas/",
                    params={"numero_apartamento": numero_apartamento},
                )
                response.raise_for_status()
                data = response.json()
                reservas = data["reservas"]
                logger.info(f"Minhas reservas: {reservas}")
                return MinhasReservasResponse(reservas=[MinhaReserva(**reserva) for reserva in reservas])
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao buscar minhas reservas: {str(e.response)}")
            return MinhasReservasResponse(reservas=[], error="Erro ao buscar minhas reservas")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar minhas reservas: {str(e)}")
            return MinhasReservasResponse(reservas=[], error="Erro inesperado ao buscar minhas reservas")
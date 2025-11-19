from datetime import date, time
from typing import Optional

import httpx
from pydantic import BaseModel


class Reservation(BaseModel):
    data: date
    hora: time
    apartamento: int
    andar: int


class Slot(BaseModel):
    start: time
    end: time
    available: bool


class ListarHorariosResponse(BaseModel):
    slots: list[Slot]
    error: Optional[str] = None


class CriarReservaResponse(BaseModel):
    is_success: bool
    message: str | None = None


class CondoAgendaApiService:
    BASE_URL = "http://localhost:8000/api"
    TIMEOUT = 30.0  # 5 seconds

    @staticmethod
    async def listar_horarios_disponiveis(
        date: date, andar: int
    ) -> ListarHorariosResponse:
        try:
            async with httpx.AsyncClient(
                timeout=CondoAgendaApiService.TIMEOUT
            ) as client:
                response = await client.get(
                    f"{CondoAgendaApiService.BASE_URL}/reservas/listar/",
                    params={"data": "2025-11-19", "andar": 0},
                )
                print(response.json())

                if response.status_code == 200:
                    data = response.json()
                    return ListarHorariosResponse(**data)

                return ListarHorariosResponse(
                    slots=[], error="Erro ao buscar horários"
                )

        except Exception as e:
            print(e)
            return ListarHorariosResponse(
                slots=[], error=f"Erro inesperado: {str(e)}"
            )

    @staticmethod
    async def criar_reserva(reservation: Reservation) -> CriarReservaResponse:
        try:
            payload = {
                "data": reservation.data.isoformat(),
                "hora": reservation.hora.isoformat(),
                "apartamento": reservation.apartamento,
                "andar": reservation.andar,
            }

            async with httpx.AsyncClient(
                timeout=CondoAgendaApiService.TIMEOUT
            ) as client:
                response = await client.post(
                    f"{CondoAgendaApiService.BASE_URL}/reservas/",
                    json=payload,
                )

                if response.status_code == 201:
                    return CriarReservaResponse(is_success=True, message=None)

                return CriarReservaResponse(
                    is_success=False,
                    message="Erro ao criar reserva",
                )
        except Exception as e:
            return CriarReservaResponse(
                is_success=False,
                message=f"Erro inesperado: {str(e)}",
            )

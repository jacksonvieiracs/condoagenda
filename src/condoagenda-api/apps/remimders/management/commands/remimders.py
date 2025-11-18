import asyncio
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import Reserva, Configuracao

from apps.remimders.whatsapp.client import WhatsAppClient

import os

EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_DEFAULT_INSTANCE = os.getenv("EVOLUTION_DEFAULT_INSTANCE")


class Command(BaseCommand):
    help = "Envia lembretes de entrada e saída para as reservas"

    def __init__(self):
        super().__init__()
        self.whatsapp_client = WhatsAppClient(
            base_url=EVOLUTION_BASE_URL,
            api_key=EVOLUTION_API_KEY,
            default_instance=EVOLUTION_DEFAULT_INSTANCE,
        )

    async def send_entrada_reminders(self, config: Configuracao):
        now = timezone.now()

        reservas = Reserva.objects.filter(
            enviar_lembrete=True,
            lembrete_entrada_enviado=False,
        )

        for reserva in reservas:
            reserva_datetime = timezone.make_aware(
                datetime.combine(reserva.data, reserva.hora)
            )

            time_diff = (reserva_datetime - now).total_seconds() / 60

            if 0 <= time_diff <= config.tempo_lembrete_entrada_minutos:
                message = (
                    f"🏊 Lembrete de Reserva\n\n"
                    f"Sua reserva no {reserva.get_andar_display()} está próxima!\n"
                    f"Data: {reserva.data.strftime('%d/%m/%Y')}\n"
                    f"Horário de entrada: {reserva.hora.strftime('%H:%M')}\n"
                    f"Apartamento: {reserva.apartamento.numero}"
                )

                try:
                    await self.whatsapp_client.send_message(
                        reserva.phone_number, message
                    )
                    reserva.lembrete_entrada_enviado = True
                    reserva.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Lembrete de entrada enviado para reserva #{reserva.id}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Erro ao enviar lembrete de entrada para reserva #{reserva.id}: {e}"
                        )
                    )

    async def send_saida_reminders(self, config: Configuracao):
        now = timezone.now()

        reservas = Reserva.objects.filter(
            enviar_lembrete=True,
            lembrete_saida_enviado=False,
        )

        for reserva in reservas:
            reserva_saida_datetime = timezone.make_aware(
                datetime.combine(reserva.data, reserva.hora_saida)
            )

            time_diff = (reserva_saida_datetime - now).total_seconds() / 60

            if 0 <= time_diff <= config.tempo_lembrete_saida_minutos:
                message = (
                    f"⏰ Lembrete de Saída\n\n"
                    f"Sua reserva no {reserva.get_andar_display()} está próxima do fim!\n"
                    f"Horário de saída: {reserva.hora_saida.strftime('%H:%M')}\n"
                    f"Por favor, organize-se para liberar o espaço."
                )

                try:
                    await self.whatsapp_client.send_message(
                        reserva.phone_number, message
                    )
                    reserva.lembrete_saida_enviado = True
                    reserva.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Lembrete de saída enviado para reserva #{reserva.id}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Erro ao enviar lembrete de saída para reserva #{reserva.id}: {e}"
                        )
                    )

    async def process_reminders(self):
        try:
            config, _ = Configuracao.objects.get_or_create(id=1)
            await self.send_entrada_reminders(config)
            await self.send_saida_reminders(config)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar lembretes: {e}"))

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando processamento de lembretes..."))
        asyncio.run(self.process_reminders())
        self.stdout.write(self.style.SUCCESS("Processamento concluído"))

import datetime
import os
from functools import lru_cache

from agendabot.modules.whatsapp.client import WhatsAppClient
from agendabot.modules.workflow.core import WorkflowStep
from agendabot.modules.workflow.entities.workflow import WorkflowData
from agendabot.modules.workflow.interfaces import (
    IOrchestratorActionHandler,
    IOrchestratorEventHandler,
    IOutputHandler,
    ITemplateMessageRender,
)
from agendabot.modules.workflow.interfaces.orchestrator_event_handler import (
    OrchestratorEvent,
)
from agendabot.modules.workflow.templates.condoagenda.service import (
    CondoAgendaApiService,
    Reservation,
)
from agendabot.modules.workflow.templates.condoagenda.workflow import (
    CondoAgendaSteps,
)

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_DEFAULT_INSTANCE = os.getenv(
    "EVOLUTION_DEFAULT_INSTANCE", "condoagenda"
)


class X(IOrchestratorEventHandler):
    async def _render_progress(self, data: WorkflowData) -> None:
        if data.workflow_id == CondoAgendaSteps.AGENDAMENTO:
            if not data.steps:
                return

            message = "Passos do agendamento\n\n"
            for step in data.steps:
                status = "✅" if step.is_done else "☑️"
                label = step.label
                if step.is_done:
                    assert step.value is not None
                    label = step.value
                step_line = f"{status} {label}"
                message += step_line + "\n"
            await self._output_handler.send_message(message)

    async def on_event(self, event: OrchestratorEvent, data: WorkflowData):
        if event in (OrchestratorEvent.WORKFLOW_PROGRESS,):
            await self._render_progress(data)

        if event in (OrchestratorEvent.WORKFLOW_ENDED,):
            print("Processo finalizado!")

        if event in (OrchestratorEvent.WORKFLOW_ENDED,):
            data_reserva = data.values.get(CondoAgendaSteps.AGENDAMENTO_DATA)
            hora_reserva = data.values.get(CondoAgendaSteps.AGENDAMENTO_HORA)
            apartamento_reserva = data.values.get(CondoAgendaSteps.APARTAMENTO)
            andar_reserva = 0

            agora = datetime.datetime.now()
            dia, mes = data_reserva.split("/")
            hora, minuto = hora_reserva.split(":")

            data_reserva = datetime.date(
                year=agora.year, month=int(mes), day=int(dia)
            )
            hora_reserva = datetime.time(hour=int(hora), minute=int(minuto))

            reserva = Reservation(
                data=data_reserva,
                hora=hora_reserva,
                apartamento=int(apartamento_reserva),
                andar=andar_reserva,
            )
            response = await CondoAgendaApiService.criar_reserva(reserva)

            # TODO: Melhorar isso deve ser um logger interno para o bot
            if response.is_success:
                print("Reserva criada com sucesso")
            else:
                print("Erro ao criar reserva")


class DefaultTemplateMessageRender(ITemplateMessageRender):
    def render_message(self, step: WorkflowStep, data: dict[str, str]) -> str:
        message = step.message

        if step.is_template:
            for key, value in data.items():
                message = step.message.replace(f"@{key}@", value)

        return message

    def render_pool(self, step: WorkflowStep, data: WorkflowData) -> str:
        title = step.title

        if step.is_template:
            for key, value in data.values.items():
                title = title.replace(f"@{key}@", value)

        message = f"*{title}*\n\n"

        for option in step.options:
            message += f"{option.id} - {option.display_value}\n"
        return message

    def render_question(self, step: WorkflowStep) -> str:
        message = step.question
        return message


class WorkflowActionHandler(IOrchestratorActionHandler):
    def __init__(
        self,
        output_handler: IOutputHandler,
        template_message_render: ITemplateMessageRender,
    ) -> None:
        self._output_handler = output_handler
        self._template_message_render = template_message_render

    async def handle_send_message(self, step: WorkflowStep, data: WorkflowData):
        message = self._template_message_render.render_message(
            step, data.values
        )
        await self._output_handler.send_message(message)

    async def handle_send_question(self, step: WorkflowStep):
        message = self._template_message_render.render_question(step)
        await self._output_handler.send_message(message)

    async def handle_send_pool(self, step: WorkflowStep, data: WorkflowData):
        message = self._template_message_render.render_pool(step, data)
        await self._output_handler.send_message(message)

    async def handle_error(self, step: WorkflowStep, input: str):
        await self._output_handler.send_message("error!")


class WaZapOutputHandler(IOutputHandler):
    def __init__(self, wpp_client: WhatsAppClient, phone_number: str) -> None:
        self._wpp_client = wpp_client
        self._phone_number = phone_number

    async def send_message(self, message: str):
        await self._wpp_client.send_plain_text_message(
            message, phone_number=self._phone_number
        )


@lru_cache()
def get_whatsapp_client() -> WhatsAppClient:
    return WhatsAppClient(
        api_key=EVOLUTION_API_KEY,
        base_url=EVOLUTION_BASE_URL,
        default_instance=EVOLUTION_DEFAULT_INSTANCE,
    )


def get_template_renderer() -> ITemplateMessageRender:
    return DefaultTemplateMessageRender()


def create_output_handler(phone_number: str) -> WaZapOutputHandler:
    wpp_client = get_whatsapp_client()
    return WaZapOutputHandler(wpp_client, phone_number)


def create_action_handler(phone_number: str) -> WorkflowActionHandler:
    output_handler = create_output_handler(phone_number)
    template_renderer = get_template_renderer()
    return WorkflowActionHandler(output_handler, template_renderer)


def create_event_handler(phone_number: str) -> IOrchestratorEventHandler:
    output_handler = create_output_handler(phone_number)
    return X(output_handler)

import asyncio
import datetime
import logging
import textwrap

from agendabot.modules.workflow.core import WorkflowStep
from agendabot.modules.workflow.entities.workflow import WorkflowData
from agendabot.modules.workflow.interfaces import IOrchestratorActionHandler
from agendabot.modules.workflow.interfaces.orchestrator_event_handler import (
    IOrchestratorEventHandler,
    OrchestratorEvent,
)
from agendabot.modules.workflow.interfaces.output_handler import IOutputHandler
from agendabot.modules.workflow.interfaces.template_message_render import (
    ITemplateMessageRender,
)
from agendabot.modules.workflow.templates.condoagenda.service import (
    CondoAgendaApiService,
    Reservation,
)
from agendabot.modules.workflow.templates.condoagenda.workflow import (
    CondoAgendaSteps,
    create_condoagenda_workflow,
)

logging.basicConfig(level=logging.INFO)


class X(IOrchestratorEventHandler):
    async def _render_progress(self, data: WorkflowData) -> None:
        # print("WORKFLOW_PROGRESS", data)
        ...

    async def on_event(self, event: OrchestratorEvent, data: WorkflowData):
        if event in (OrchestratorEvent.WORKFLOW_PROGRESS,):
            await self._render_progress(data)

        if event in (OrchestratorEvent.WORKFLOW_ENDED,):
            data_reserva = data.values.get(CondoAgendaSteps.AGENDAMENTO_DATA)
            hora_reserva = data.values.get(CondoAgendaSteps.AGENDAMENTO_HORA)
            apartamento_reserva = data.values.get(CondoAgendaSteps.APARTAMENTO)
            andar_reserva = 0

            # Só deve executar essa lógica de criação caso ele tenha passo pelos passos de agendamento (desafio: verificar se ele passou pelo workflow de agendamento)
            # Ele não deve criar a reserva apenas quando chegar no final do workflow, mas sim quando ele passos pelos passos de agendamento. o usuario pode ficar em tempo inderminado sem temrinar o workflow 
            # se seguir essa logica.
            if not data_reserva or not hora_reserva or not apartamento_reserva:
                print("❌ Erro ao criar reserva: dados incompletos")
                return

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
            if response.is_success:
                print("Reserva criada com sucesso")
            else:
                print("Erro ao criar reserva")
                print(response.message)


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
    ):
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


class CliOutputHandler(IOutputHandler):
    async def send_message(self, message: str):
        self.__print_box(message, 40, "left")

    def __print_box(
        self, message: str, max_width: int = 40, align: str = "center"
    ):
        print("BOT")
        print("+" + "-" * (max_width + 2) + "+")
        raw_lines = message.strip().split("\n")

        wrapped_lines = []
        for line in raw_lines:
            wrapped = textwrap.wrap(line, width=max_width - 2 - 2) or [""]
            wrapped_lines.extend(wrapped)

        for line in wrapped_lines:
            if align == "left":
                text = line.ljust(max_width)
            elif align == "right":
                text = line.rjust(max_width)
            else:
                text = line.center(max_width)
            print("|" + " " + text + " " + "|")

        print("+" + "-" * (max_width + 2) + "+" + "\n")


def should_start_workflow(input: str) -> bool:
    input_lower = input.lower()
    return input_lower in ("#iniciar", "#agendar")


def should_finish_workflow(input: str) -> bool:
    input_lower = input.lower()
    return input_lower in ("#encerrar")


async def main_async():
    cli_output_handler = CliOutputHandler()
    event_handler = X(cli_output_handler)
    default_template_renderer = DefaultTemplateMessageRender()
    workflow_action_handler = WorkflowActionHandler(
        output_handler=cli_output_handler,
        template_message_render=default_template_renderer,
    )
    orchestrator = create_condoagenda_workflow(
        event_handler, workflow_action_handler
    )

    while True:
        user_input = await asyncio.to_thread(input, "USER: ")
        if should_finish_workflow(user_input):
            break

        if not orchestrator.is_started and should_start_workflow(user_input):
            await orchestrator.start()
            continue

        if orchestrator.is_finished():
            break

        if orchestrator.is_started:
            await orchestrator.process(user_input)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

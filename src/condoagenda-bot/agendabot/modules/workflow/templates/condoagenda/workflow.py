from datetime import datetime, timedelta
from enum import StrEnum, unique

from agendabot.modules.workflow.core import (
    Workflow,
    WorkflowStep,
    WorkflowStepBehavior,
)
from agendabot.modules.workflow.factories.workflow import (
    PoolBuilder,
    WorkflowStepFactory,
)
from agendabot.modules.workflow.interfaces import IOrchestratorActionHandler
from agendabot.modules.workflow.interfaces.orchestrator_event_handler import (
    IOrchestratorEventHandler,
)
from agendabot.modules.workflow.orchestrator import WorkflowOrchestrator

from .service import CondoAgendaApiService


@unique
class CondoAgendaSteps(StrEnum):
    BOAS_VINDAS = "boas_vindas"

    APARTAMENTO = "apartamento"

    MENU = "menu"

    # workflow agendamento
    AGENDAMENTO = "agendamento"
    AGENDAMENTO_ANDAR = "bloco"
    AGENDAMENTO_DATA = "data"
    AGENDAMENTO_HORA = "hora"
    AGENDAMENTO_RESUMO = "agendamento_resumo"
    AGENDAMENTO_CONFIRMACAO = "agendamento_confirmacao"
    AGENDAMENTO_REINICIAR = "agendamento_reiniciar"
    AGENDAMENTO_CANCELAR = "agendamento_cancelar"

    # workflow meus agendamentos
    MEUS_AGENDAMENTOS = "meus_agendamentos"


def create_boas_vindas_step(step_factory: WorkflowStepFactory):
    step = step_factory.create_send_message(
        id=CondoAgendaSteps.BOAS_VINDAS,
        name="Boas vindas",
        message="Olá! Sou o assistente virtual do condomínio. Posso te ajudar com:\n\n"
        "• Realizar agendamentos\n"
        "• Ver seus agendamentos\n\n"
        "É simples: escolha uma opção no menu e siga as instruções. "
        "A qualquer momento, digite *#encerrar* para finalizar.",
    )
    step.id = CondoAgendaSteps.BOAS_VINDAS
    return step


def create_menu_step():
    step = (
        PoolBuilder()
        .decision()
        .with_id(CondoAgendaSteps.MENU)
        .with_question("O que você deseja fazer?")
        .with_name("Menu")
        .with_option(
            "Agendamento",
            display_value="📅 Realizar agendamento",
            reference_id=CondoAgendaSteps.AGENDAMENTO,
        )
        .with_option(
            "Meus agendamentos",
            display_value="🔍 Meus agendamentos",
            reference_id=CondoAgendaSteps.MEUS_AGENDAMENTOS,
        )
        .build()
    )
    return step


async def load_resumo_agendamento(
    values: dict[str, str] | None,
) -> WorkflowStep:
    if not values:
        values = {}

    apartamento = values.get(CondoAgendaSteps.APARTAMENTO, "")
    data = values.get(CondoAgendaSteps.AGENDAMENTO_DATA, "")
    hora = values.get(CondoAgendaSteps.AGENDAMENTO_HORA, "")

    resume_message = (
        f"*Apartamento:* {apartamento}\n\n"
        "✅ Agendamento realizado com sucesso\n"
        f"✅ {data}\n"
        f"✅ {hora}\n"
    )

    step = WorkflowStepFactory().create_send_message(
        id=CondoAgendaSteps.AGENDAMENTO_RESUMO,
        name="Resumo do Agendamento",
        message=resume_message,
    )

    return step


async def load_dates_for_next_7_days(
    values: dict[str, str] | None = None,
) -> WorkflowStep:
    now = datetime.now()
    today = now.date()
    dates = []

    weekdays = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]

    for i in range(7):
        date = now + timedelta(days=i)
        date_only = date.date()
        weekday = weekdays[date.weekday()]

        if date_only == today:
            description = "Hoje"
        elif date_only == today + timedelta(days=1):
            description = "Amanhã"
        else:
            description = weekday

        date_value = date.strftime("%d/%m")
        date_display = f"{date_value} ({description})"
        dates.append((date_value, date_display))

    step = (
        PoolBuilder().with_name("Data").with_question("Qual data você prefere?")
    )

    for date_value, date_display in dates:
        step = step.with_option(date_value, display_value=date_display)

    return step.build()


SLOT_DURATION_MINUTES = 120


async def load_hours_for_current_date(
    values: dict[str, str] | None = None,
) -> WorkflowStep:
    data = values.get(CondoAgendaSteps.AGENDAMENTO_DATA, "")
    andar = 0

    day, month = data.split("/")
    data_with_year = datetime(
        year=datetime.now().year, month=int(month), day=int(day)
    ).date()

    response = await CondoAgendaApiService.listar_horarios_disponiveis(
        date=data_with_year, andar=andar
    )

    step = (
        PoolBuilder()
        .with_name("Hora")
        .with_question("Qual horário você prefere?")
    )

    for slot in response.slots:
        if slot.available:
            step = step.with_option(
                slot.start,
                display_value=str(slot),
            )

    return step.build()


def create_confirmacao_agendamento_workflow(
    step_factory: WorkflowStepFactory,
) -> Workflow:
    workflow = Workflow(id=CondoAgendaSteps.AGENDAMENTO_CONFIRMACAO)
    step = step_factory.create_send_message(
        id=CondoAgendaSteps.AGENDAMENTO_CONFIRMACAO,
        name="Confirmação de agendamento",
        message="✅ *Agendamento realizado com sucesso.*\n\n"
        "Caso deseje realizar outro agendamento, basta digitar #AGENDAR para voltar ao menu inicial\n\n"
        "Obrigado pela preferência!",
    )
    workflow.add_steps([step])
    return workflow


def create_reiniciar_atendimento_workflow(
    step_factory: WorkflowStepFactory,
) -> Workflow:
    workflow = Workflow(id=CondoAgendaSteps.AGENDAMENTO_REINICIAR)
    step = step_factory.create_send_message(
        id=CondoAgendaSteps.AGENDAMENTO_REINICIAR,
        behavior=WorkflowStepBehavior.RESTART_WORKFLOW,
        name="Reinício de atendimento",
        message="Atendimento reiniciado com sucesso!",
    )
    workflow.add_steps([step])
    return workflow


def create_agendamento_workflow(step_factory: WorkflowStepFactory) -> Workflow:
    workflow = Workflow(id=CondoAgendaSteps.AGENDAMENTO)

    step_data = (
        PoolBuilder()
        .lazy()
        .with_id(CondoAgendaSteps.AGENDAMENTO_DATA)
        .with_name("Escolher data")
        .with_question("Qual data você prefere?")
        .with_mount(load_dates_for_next_7_days)
        .build()
    )

    step_hora = (
        PoolBuilder()
        .lazy()
        .with_id(CondoAgendaSteps.AGENDAMENTO_HORA)
        .with_name("Escolher horário")
        .with_question("Qual horário você prefere?")
        .with_mount(load_hours_for_current_date)
        .build()
    )

    step_resumo = step_factory.create_send_message(
        id=CondoAgendaSteps.AGENDAMENTO_RESUMO,
        name="Resumo do Agendamento",
        message="",
        is_template=False,
        is_lazy=True,
    )
    step_resumo.set_mount(load_resumo_agendamento)

    step_confirmacao = (
        PoolBuilder()
        .decision()
        .with_id(CondoAgendaSteps.AGENDAMENTO_CONFIRMACAO)
        .with_workflow_id(CondoAgendaSteps.AGENDAMENTO_CONFIRMACAO)
        .with_name("Confirmação")
        .with_question("Deseja confirmar este agendamento?")
        .with_option(
            "Confirmar",
            display_value="✅ Confirmar",
            reference_id=CondoAgendaSteps.AGENDAMENTO_CONFIRMACAO,
        )
        .with_option(
            "Reiniciar",
            display_value="🔄 Reiniciar",
            reference_id=CondoAgendaSteps.AGENDAMENTO_REINICIAR,
        )
        .build()
    )

    workflow.add_steps(
        [
            step_data,
            step_hora,
            step_resumo,
            step_confirmacao,
        ]
    )
    return workflow


def create_precos_workflow(step_factory: WorkflowStepFactory) -> Workflow:
    workflow = Workflow(id=CondoAgendaSteps.PRECOS)
    step = step_factory.create_send_message(
        id=CondoAgendaSteps.PRECOS,
        workflow_id=CondoAgendaSteps.PRECOS,
        name="Preços",
        message="Aqui estão nossos preços...",
    )
    workflow.add_steps([step])
    return workflow


def create_endereco_workflow(step_factory: WorkflowStepFactory) -> Workflow:
    workflow = Workflow(id=CondoAgendaSteps.ENDERECO)
    step = step_factory.create_send_message(
        id=CondoAgendaSteps.ENDERECO,
        workflow_id=CondoAgendaSteps.ENDERECO,
        name="Endereço",
        message="Nosso endereço é...",
    )
    workflow.add_steps([step])
    return workflow


def create_meus_agendamentos_workflow(
    step_factory: WorkflowStepFactory,
) -> Workflow:
    workflow = Workflow(id=CondoAgendaSteps.MEUS_AGENDAMENTOS)
    step = step_factory.create_send_message(
        id=CondoAgendaSteps.MEUS_AGENDAMENTOS,
        name="Meus agendamentos",
        message="Aqui estão seus agendamentos...",
    )
    step.id = CondoAgendaSteps.MEUS_AGENDAMENTOS
    workflow.add_steps([step])
    return workflow


def create_condoagenda_workflow(
    event_handler: IOrchestratorEventHandler,
    action_handler: IOrchestratorActionHandler,
) -> WorkflowOrchestrator:
    workflow_orchestrator = WorkflowOrchestrator(
        event_handler=event_handler, action_handler=action_handler
    )
    step_factory = WorkflowStepFactory()

    step_boas_vindas = create_boas_vindas_step(step_factory)

    step_apartamento = step_factory.create_question(
        id=CondoAgendaSteps.APARTAMENTO,
        name="Escolher apartamento",
        question="Digite o número seu apartamento. ex. 101, 118",
    )

    step_menu = create_menu_step()

    workflow_agendamento = create_agendamento_workflow(step_factory)
    workflow_meus_agendamentos = create_meus_agendamentos_workflow(step_factory)

    workflow_confirmacao_agendamento = create_confirmacao_agendamento_workflow(
        step_factory
    )
    workflow_reiniciar_atendimento = create_reiniciar_atendimento_workflow(
        step_factory
    )

    workflow_orchestrator.load(
        [
            workflow_agendamento,
            workflow_meus_agendamentos,
            workflow_confirmacao_agendamento,
            workflow_reiniciar_atendimento,
        ]
    )

    workflow_orchestrator.add_step(step_boas_vindas)
    workflow_orchestrator.add_step(step_apartamento)
    workflow_orchestrator.add_step(step_menu)
    return workflow_orchestrator

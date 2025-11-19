from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Self

from .entities.workflow import WorkflowData


class WorkflowStepAction(Enum):
    SEND_POOL = 0  # should await for user response
    SEND_TEXT_MESSAGE = 1  # informative
    SEND_QUESTION = 2  # question should await for user response


# behaviour execute after the step is processed
class WorkflowStepBehavior(Enum):
    RESTART_WORKFLOW = (
        0  # if true, the step restart the workflow to the initial step
    )
    END_WORKFLOW = 1  # if true, the step finalize the workflow
    NONE = 2  # if true, the step does nothing


@dataclass
class WorkflowOption:
    id: int
    value: str
    display_value: str
    is_internal_back_action: bool = False
    reference_id: str = ""


@dataclass
class WorkflowStep:
    id: str

    workflow_id: str = field(default="", init=False)

    name: str
    action: WorkflowStepAction

    # SEND_POOL
    title: str = ""
    selected_option_id: int | None = None
    options: list[WorkflowOption] = field(default_factory=list)

    # SEND_TEXT_MESSAGE
    message: str = ""

    # SEND_QUESTION
    question: str = ""
    value: str | None = None

    metadata: str = ""

    # envio de confirmacao, status do agendamento, inicio do agendamento, conclusao do agendamento (internas)
    # são consideradas por exemplo etapas internas, não são mostradas para o usuário mas servem pipeline de controle interno
    is_internal: bool = False
    is_template: bool = False
    is_decision: bool = False

    behavior: WorkflowStepBehavior = WorkflowStepBehavior.NONE

    # controll if node should be mounter on peek
    is_lazy: bool = False

    _callback: Callable[[str], None] | None = None
    _mount: Awaitable[Callable[[dict[str, str] | None], Self]] | None = None

    def __str__(self):
        return self.name

    @property
    def is_pool(self):
        return self.action == WorkflowStepAction.SEND_POOL

    @property
    def is_send_message(self):
        return self.action == WorkflowStepAction.SEND_TEXT_MESSAGE

    @property
    def is_question(self):
        return self.action == WorkflowStepAction.SEND_QUESTION

    # -- Getters --
    def get_selected_option(self, option_id: int) -> WorkflowOption | None:
        for option in self.options:
            if option.id == option_id:
                return option
        return None

    # -- Setters --
    def set_answer(self, answer: str):
        self.value = answer

    def set_selected_option(self, option: WorkflowOption):
        self.selected_option_id = option.id
        self.value = option.value

    def set_mount(self, data_loader: Callable[[dict[str, str] | None], Self]):
        self._mount = data_loader

    def validate_input(self, input_value: str) -> bool:
        if self.is_pool:
            try:
                option_id = int(input_value)
                option = self.get_selected_option(option_id)
                return option is not None
            except ValueError:
                return False

        if self.is_question:
            return bool(input_value.strip())

        return True

    ## -- Actions --
    async def mount(self, data: WorkflowData | None = None):
        if self._mount:
            step = await self._mount(data.values)
            if step.options:
                self.options = step.options
            if step.message:
                self.message = step.message
                self.workflow_id = step.workflow_id


class Workflow:
    def __init__(self, id: str) -> None:
        self.id = id
        self.steps: list[WorkflowStep] = []

    def add_steps(self, steps: list[WorkflowStep]):
        self.steps = steps

    def size(self):
        return len(self.steps)

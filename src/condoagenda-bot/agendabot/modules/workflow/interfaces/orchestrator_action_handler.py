from abc import ABC, abstractmethod

from agendabot.modules.workflow.core import WorkflowStep
from agendabot.modules.workflow.interfaces.template_message_render import (
    ITemplateMessageRender,
)

from ..entities.workflow import WorkflowData
from .output_handler import IOutputHandler


class IOrchestratorActionHandler(ABC):
    @abstractmethod
    def __init__(
        self,
        output_handler: IOutputHandler,
        template_render: ITemplateMessageRender,
    ) -> None:
        self._output_handler = output_handler
        self._template_render = template_render

    @abstractmethod
    async def handle_send_message(
        self, step: WorkflowStep, data: WorkflowData
    ): ...

    @abstractmethod
    async def handle_send_pool(
        self, step: WorkflowStep, data: WorkflowData
    ): ...

    @abstractmethod
    async def handle_send_question(self, step: WorkflowStep): ...

    @abstractmethod
    async def handle_error(self, step: WorkflowStep, input: str): ...

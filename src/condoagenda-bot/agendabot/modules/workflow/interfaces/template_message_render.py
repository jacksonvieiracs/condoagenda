from abc import ABC, abstractmethod

from agendabot.modules.workflow.core import WorkflowStep
from agendabot.modules.workflow.entities.workflow import WorkflowData


class ITemplateMessageRender(ABC):
    @abstractmethod
    def render_message(
        self, step: WorkflowStep, data: dict[str, str]
    ) -> str: ...

    @abstractmethod
    def render_pool(self, step: WorkflowStep, data: WorkflowData) -> str: ...

    @abstractmethod
    def render_question(self, step: WorkflowStep) -> str: ...

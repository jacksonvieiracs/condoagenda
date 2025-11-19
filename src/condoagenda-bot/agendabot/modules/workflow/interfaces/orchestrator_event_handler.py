from abc import ABC, abstractmethod
from enum import Enum

from ..entities.workflow import WorkflowData
from .output_handler import IOutputHandler


class OrchestratorEvent(Enum):
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_ENDED = "workflow_ended"
    WORKFLOW_PROGRESS = "workflow_progress"


class IOrchestratorEventHandler(ABC):
    def __init__(self, output_handler: IOutputHandler) -> None:
        self._output_handler = output_handler
        super().__init__()

    @abstractmethod
    async def on_event(self, event: OrchestratorEvent, data: WorkflowData): ...

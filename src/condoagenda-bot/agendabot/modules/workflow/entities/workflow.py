from dataclasses import dataclass, field


@dataclass
class StepInfo:
    name: str
    label: str
    is_done: bool
    value: str | None = None


@dataclass
class WorkflowData:
    total_nodes: int
    processed_nodes: int
    values: dict[str, str]
    progress: float
    is_finished: bool
    steps: list[StepInfo] = field(default_factory=list)

    is_awaiting_input: bool = False
    current_step_id: str | None = None
    workflow_id: str | None = None

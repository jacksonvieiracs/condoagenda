from collections import deque
from enum import Enum

from .core import (
    Workflow,
    WorkflowOption,
    WorkflowStep,
    WorkflowStepAction,
    WorkflowStepBehavior,
)
from .entities.workflow import StepInfo, WorkflowData
from .interfaces import (
    IOrchestratorActionHandler,
    IOrchestratorEventHandler,
    OrchestratorEvent,
)


class WorkflowState(Enum):
    INITIAL = 0  # before started
    DEFAULT = 1  # started
    AWAITING_INPUT = 2  # waiting for user input to continue


class WorkflowOrchestrator:
    def __init__(
        self,
        action_handler: IOrchestratorActionHandler,
        event_handler: IOrchestratorEventHandler,
    ) -> None:
        self._action_handler = action_handler
        self._event_handler = event_handler
        self._pipeline_queue = deque[WorkflowStep]()
        self._stack_processed_nodes: list[WorkflowStep] = []
        self.state: WorkflowState = WorkflowState.DEFAULT
        self._workflows: dict[str, Workflow] = {}

        self.is_started: bool = False

    def load(self, workflows: list[Workflow]):
        for workflow in workflows:
            self._workflows[workflow.id] = workflow

    def is_finished(self):
        return self.size() == 0

    def size(self):
        return len(self._pipeline_queue)

    def add_step(self, step: WorkflowStep):

        self._pipeline_queue.append(step)

    def add_workflow(self, workflow: Workflow):
        self._pipeline_queue.extend(workflow.steps)

    def peek(self):
        if len(self._pipeline_queue) == 0:
            return None

        return self._pipeline_queue[0]

    def back(self):
        last_step = self._stack_processed_nodes.pop()
        self.state = WorkflowState.DEFAULT
        self._pipeline_queue.appendleft(last_step)

    async def next(self):
        first = self._pipeline_queue.popleft()
        self._stack_processed_nodes.append(first)
        self.state = WorkflowState.DEFAULT

        if first.behavior == WorkflowStepBehavior.RESTART_WORKFLOW:
            self.clear()

        await self._event_handler.on_event(
            OrchestratorEvent.WORKFLOW_PROGRESS, self.get_data()
        )

        return self.peek()

    def await_input(self):
        self.state = WorkflowState.AWAITING_INPUT

    async def start(self):
        self.is_started = True
        await self._event_handler.on_event(
            OrchestratorEvent.WORKFLOW_STARTED, self.get_data()
        )
        await self.process(None)

    def clear(self):
        for item in self._stack_processed_nodes:
            self._pipeline_queue.append(item)
            # only at the first decision node
            if item.is_decision:
                break
        self._stack_processed_nodes.clear()
        self.is_started = False

    async def handle_send_message(self, current_step: WorkflowStep):
        await self._action_handler.handle_send_message(
            current_step, self.get_data()
        )

    def get_data(self) -> WorkflowData:
        """
        Returns the resume of current state of all processed nodes in the orchestrator
        with some addional stats like total of nodes, total of processed nodes, progress, ...
        """

        values: dict[str, str] = {}
        steps_info: list[StepInfo] = []

        for node in self._stack_processed_nodes:
            if node.is_send_message or node.is_internal:
                continue
            if node.value:
                values[node.id] = node.value
                steps_info.append(
                    StepInfo(
                        name=node.name,
                        label=node.name,
                        is_done=True,
                        value=node.value,
                    )
                )

        for node in self._pipeline_queue:
            if node.is_send_message or node.is_internal:
                continue
            steps_info.append(
                StepInfo(
                    name=node.name,
                    label=node.name,
                    is_done=False,
                    value=None,
                )
            )

        current_step = self.peek()
        current_step_id = current_step.id if current_step else None
        workflow_id = current_step.workflow_id if current_step else None

        total_nodes = len(self._pipeline_queue) + len(
            self._stack_processed_nodes
        )
        processed_nodes = len(self._stack_processed_nodes)
        progress = processed_nodes / total_nodes if total_nodes > 0 else 1.0

        data = WorkflowData(
            total_nodes=total_nodes,
            processed_nodes=processed_nodes,
            is_finished=self.is_finished(),
            values=values,
            progress=progress,
            steps=steps_info,
            is_awaiting_input=self.state == WorkflowState.AWAITING_INPUT,
            current_step_id=current_step_id,
            workflow_id=workflow_id,
        )

        return data

    async def process(self, value: str | None):
        current_step = self.peek()

        if not self.is_started:
            await self.start()
            return

        is_ended = self.is_started and current_step is None
        if is_ended:
            await self._event_handler.on_event(
                OrchestratorEvent.WORKFLOW_ENDED, self.get_data()
            )
            return

        if not current_step:
            return

        if current_step.is_lazy:
            await current_step.mount(self.get_data())

        cleaned_input = value.strip() if value else ""

        if (
            self.state == WorkflowState.AWAITING_INPUT
            and not current_step.validate_input(cleaned_input)
        ):
            return

        match current_step.action:
            case WorkflowStepAction.SEND_TEXT_MESSAGE:
                await self.handle_send_message(current_step)
                _ = await self.next()
                await self.process(None)

            case WorkflowStepAction.SEND_POOL:
                if self.state == WorkflowState.DEFAULT:
                    await self._action_handler.handle_send_pool(
                        step=current_step, data=self.get_data()
                    )
                    self.await_input()
                else:
                    selected_option = current_step.get_selected_option(
                        int(cleaned_input)
                    )

                    if not selected_option:
                        # TODO: Handle error of invalid option selected (exception like message)
                        return

                    if selected_option.is_internal_back_action:
                        self.back()
                        await self.process(None)
                    else:
                        current_step.set_selected_option(selected_option)

                        if current_step.is_decision:
                            new_workflow = self._workflows.get(
                                selected_option.reference_id
                            )
                            assert new_workflow, "Decision workflow not found"
                            if new_workflow:
                                self.add_workflow(new_workflow)

                        _ = await self.next()
                        await self.process(None)

            case WorkflowStepAction.SEND_QUESTION:
                if self.state == WorkflowState.DEFAULT:
                    await self._action_handler.handle_send_question(
                        current_step
                    )
                    self.await_input()
                else:
                    current_step.set_answer(cleaned_input)
                    _ = await self.next()
                    await self.process(None)

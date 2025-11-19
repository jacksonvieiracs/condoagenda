from typing import Awaitable, Callable

from ...workflow.core import (
    WorkflowOption,
    WorkflowStep,
    WorkflowStepAction,
    WorkflowStepBehavior,
)


class WorkflowStepFactory:
    @staticmethod
    def create_pool(
        id: str,
        name: str,
        title: str,
        options: list[WorkflowOption],
        is_decision: bool = False,
        is_lazy: bool = False,
        behavior: WorkflowStepBehavior = WorkflowStepBehavior.NONE,
    ):
        return WorkflowStep(
            id=id,
            name=name,
            title=title,
            options=options,
            is_decision=is_decision,
            action=WorkflowStepAction.SEND_POOL,
            is_internal=False,
            is_lazy=is_lazy,
            behavior=behavior,
        )

    @staticmethod
    def create_send_message(
        id: str,
        name: str,
        message: str,
        behavior: WorkflowStepBehavior = WorkflowStepBehavior.NONE,
        is_template: bool = False,
        is_lazy: bool = False,
    ):
        return WorkflowStep(
            id=id,
            name=name,
            message=message,
            is_internal=False,
            action=WorkflowStepAction.SEND_TEXT_MESSAGE,
            behavior=behavior,
            is_template=is_template,
            is_lazy=is_lazy,
        )

    @staticmethod
    def create_question(id: str, name: str, question: str):
        return WorkflowStep(
            id=id,
            name=name,
            question=question,
            is_internal=False,
            action=WorkflowStepAction.SEND_QUESTION,
        )


class PoolBuilder:
    def __init__(self):
        self._factory = WorkflowStepFactory()
        self._id = ""
        self._workflow_id = ""
        self._name = ""
        self._question = ""
        self._is_decision = False
        self._is_lazy = False
        self._data_loader: Awaitable[Callable[[dict[str, str] | None], WorkflowStep]] | None = None
        self._behavior: WorkflowStepBehavior = WorkflowStepBehavior.NONE
        self._options = []

    def with_name(self, name: str):
        self._name = name
        return self

    def decision(self):
        self._is_decision = True
        return self

    def lazy(self):
        self._is_lazy = True
        return self

    def with_question(self, name: str):
        self._question = name
        return self

    def with_id(self, id: str):
        self._id = id
        return self

    def with_workflow_id(self, workflow_id: str):
        self._workflow_id = workflow_id
        return self

    def with_option(
        self,
        value: str,
        display_value: str | None = None,
        reference_id: str = "",
    ):
        if display_value is None:
            display_value = value

        option = WorkflowOption(
            id=len(self._options),
            value=value,
            reference_id=reference_id,
            display_value=display_value,
        )
        self._options.append(option)
        return self

    def with_behavior(self, behavior: WorkflowStepBehavior):
        self._behavior = behavior
        return self

    def with_mount(
        self,
        data_loader: Awaitable[Callable[[dict[str, str] | None], WorkflowStep]],
    ):
        self._data_loader = data_loader
        return self

    def build(self) -> WorkflowStep:
        pool = self._factory.create_pool(
            self._id,
            self._name,
            self._question,
            self._options,
            self._is_decision,
            is_lazy=self._is_lazy,
            behavior=self._behavior,
        )

        if self._data_loader:
            pool.set_mount(data_loader=self._data_loader)

        return pool

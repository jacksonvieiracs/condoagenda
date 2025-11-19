from enum import StrEnum, unique
from unittest.mock import Mock

import pytest

from agendabot.modules.workflow.core import (
    Workflow,
    WorkflowStep,
)
from agendabot.modules.workflow.entities.workflow import WorkflowData
from agendabot.modules.workflow.factories.workflow import (
    PoolBuilder,
    WorkflowStepFactory,
)
from agendabot.modules.workflow.interfaces import (
    IOrchestratorActionHandler,
    IOrchestratorEventHandler,
    IOutputHandler,
    ITemplateMessageRender,
)
from agendabot.modules.workflow.orchestrator import (
    WorkflowOrchestrator,
    WorkflowState,
)


@unique
class TestStepIds(StrEnum):
    __test__ = False

    WELCOME = "welcome"
    STEP1 = "step1"
    STEP2 = "step2"
    POOL_STEP = "pool_step"
    DECISION_STEP = "decision_step"
    LAZY_POOL_STEP = "lazy_pool_step"
    WORKFLOW_DECISION = "workflow_decision"


@unique
class TestWorkflowIds(StrEnum):
    __test__ = False

    MAIN = "main"
    TEST_WORKFLOW_1 = "test-workflow-1"
    TEST_WORKFLOW_2 = "test-workflow-2"


class FakeWorkflowActionHandler(IOrchestratorActionHandler):
    def __init__(
        self,
        output_handler: IOutputHandler,
        template_render: ITemplateMessageRender,
    ) -> None:
        self._output_handler = output_handler
        self._template_render = template_render

    def handle_send_message(
        self, step: WorkflowStep, data: WorkflowData
    ) -> None: ...

    def handle_send_template_message(
        self, step: WorkflowStep, workflow: Workflow
    ) -> None: ...

    def handle_send_question(self, step: WorkflowStep) -> None: ...

    def handle_send_pool(
        self, step: WorkflowStep, data: WorkflowData
    ) -> None: ...

    def handle_progress(self, workflow: Workflow) -> None: ...

    def handle_error(self, step: WorkflowStep, input: str) -> None: ...


def create_test_send_message(
    step_factory: WorkflowStepFactory,
    step_id: str,
    workflow_id: str,
    message: str,
) -> WorkflowStep:
    return step_factory.create_send_message(
        id=step_id,
        workflow_id=workflow_id,
        name=step_id,
        message=message,
    )


def create_test_pool_step(
    step_id: str,
    workflow_id: str,
    question: str,
    name: str,
    options: list[tuple[str, str]] | None = None,
    is_decision: bool = False,
) -> WorkflowStep:
    builder = (
        PoolBuilder()
        .with_id(step_id)
        .with_workflow_id(workflow_id)
        .with_question(question)
        .with_name(name)
    )

    if is_decision:
        builder = builder.decision()

    if options:
        for option_value, reference_id in options:
            builder = builder.with_option(option_value, reference_id)
    else:
        builder = (
            builder.with_option("python")
            .with_option("javascript")
            .with_option("c#")
        )

    return builder.build()


@pytest.fixture
def output_handler():
    return Mock(spec=IOutputHandler)


@pytest.fixture
def template_render():
    return Mock(spec=ITemplateMessageRender)


@pytest.fixture
def event_handler():
    return Mock(spec=IOrchestratorEventHandler)


@pytest.fixture
def orchestrator(
    output_handler: IOutputHandler,
    template_render: ITemplateMessageRender,
    event_handler: IOrchestratorEventHandler,
) -> WorkflowOrchestrator:
    return WorkflowOrchestrator(
        action_handler=FakeWorkflowActionHandler(
            output_handler, template_render
        ),
        event_handler=event_handler,
    )


@pytest.fixture
def step_factory():
    return WorkflowStepFactory()


@pytest.fixture
def pool_step():
    return create_test_pool_step(
        step_id=TestStepIds.POOL_STEP,
        workflow_id=TestWorkflowIds.MAIN,
        question="what is the best programming language",
        name="best programming language",
    )


class TestWorkflowOrchestrator:
    def test_initial_state_should_be_empty(
        self, orchestrator: WorkflowOrchestrator
    ):
        assert orchestrator.is_finished()

    def test_should_add_step(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
    ):
        welcome_step = create_test_send_message(
            step_factory, TestStepIds.WELCOME, TestWorkflowIds.MAIN, "Hi!"
        )
        orchestrator.add_step(welcome_step)

        assert orchestrator.size() == 1

        first = orchestrator.peek()
        assert first is not None
        assert first.is_send_message

    def test_next_should_avance_populate_processed_stack(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
    ):
        step1 = create_test_send_message(
            step_factory, TestStepIds.STEP1, TestWorkflowIds.MAIN, "Hi!"
        )
        step2 = create_test_send_message(
            step_factory, TestStepIds.STEP2, TestWorkflowIds.MAIN, "Hi!"
        )

        orchestrator.add_step(step1)
        orchestrator.add_step(step2)

        assert orchestrator.size() == 2

        first = orchestrator.next()
        assert first is not None
        assert first.message == step1.message
        assert orchestrator.size() == 1

    def test_back_should_rollback_the_last_processed_to_queue(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
    ):
        step1 = create_test_send_message(
            step_factory, TestStepIds.STEP1, TestWorkflowIds.MAIN, "Hi!"
        )
        step2 = create_test_send_message(
            step_factory, TestStepIds.STEP2, TestWorkflowIds.MAIN, "Hi!"
        )

        orchestrator.add_step(step1)
        orchestrator.add_step(step2)
        assert orchestrator.size() == 2

        _ = orchestrator.next()
        assert orchestrator.size() == 1

        orchestrator.back()
        assert orchestrator.size() == 2

        first = orchestrator.peek()
        assert first is not None
        assert first.message == step1.message

    def test_process_only_with_send_messages_steps_should_advance_automatically(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
    ):
        step1 = create_test_send_message(
            step_factory, TestStepIds.STEP1, TestWorkflowIds.MAIN, "Hi!"
        )
        step2 = create_test_send_message(
            step_factory, TestStepIds.STEP2, TestWorkflowIds.MAIN, "Hi!"
        )

        orchestrator.add_step(step1)
        orchestrator.add_step(step2)
        assert orchestrator.size() == 2

        _ = orchestrator.process(None)
        assert orchestrator.is_finished()

    def test_process_with_pool_should_await_input_to_advance(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
        pool_step: WorkflowStep,
    ):
        step1 = create_test_send_message(
            step_factory, TestStepIds.STEP1, TestWorkflowIds.MAIN, "Hi!"
        )

        orchestrator.add_step(step1)
        orchestrator.add_step(pool_step)
        assert orchestrator.size() == 2

        _ = orchestrator.process(None)
        assert not orchestrator.is_finished()
        assert orchestrator.state == WorkflowState.AWAITING_INPUT

        _ = orchestrator.process("0")
        assert orchestrator.is_finished()

    def test_process_with_decision_pool_should_add_new_workflow(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
        pool_step: WorkflowStep,
    ):
        step1 = create_test_send_message(
            step_factory, TestStepIds.STEP1, TestWorkflowIds.MAIN, "Hi!"
        )
        orchestrator.add_step(step1)

        workflow1 = Workflow(id=TestWorkflowIds.TEST_WORKFLOW_1)
        workflow1.add_steps([pool_step])

        workflow2 = Workflow(id=TestWorkflowIds.TEST_WORKFLOW_2)
        workflow2_step1 = create_test_send_message(
            step_factory,
            TestStepIds.STEP1,
            TestWorkflowIds.TEST_WORKFLOW_2,
            "Hi!",
        )
        workflow2_step2 = create_test_send_message(
            step_factory,
            TestStepIds.STEP2,
            TestWorkflowIds.TEST_WORKFLOW_2,
            "Hi!",
        )
        workflow2.add_steps([workflow2_step1, workflow2_step2])

        orchestrator.load([workflow1, workflow2])

        step_decision = create_test_pool_step(
            step_id=TestStepIds.WORKFLOW_DECISION,
            workflow_id=TestWorkflowIds.MAIN,
            question="Choice a workflow to follow",
            name="workflow decision",
            options=[
                ("workflow 1", TestWorkflowIds.TEST_WORKFLOW_1),
                ("workflow 2", TestWorkflowIds.TEST_WORKFLOW_2),
            ],
            is_decision=True,
        )

        orchestrator.add_step(step_decision)
        assert orchestrator.size() == 2

        orchestrator.process(None)
        assert orchestrator.state == WorkflowState.AWAITING_INPUT

        orchestrator.process("0")

        assert orchestrator.size() == 1
        assert orchestrator.state == WorkflowState.AWAITING_INPUT

    def test_process_with_decision_pool_should_add_new_workflow_2(
        self,
        orchestrator: WorkflowOrchestrator,
        step_factory: WorkflowStepFactory,
        pool_step: WorkflowStep,
    ):
        orchestrator.add_step(
            create_test_send_message(
                step_factory, TestStepIds.STEP2, TestWorkflowIds.MAIN, "Hi!"
            )
        )

        workflow1 = Workflow(id=TestWorkflowIds.TEST_WORKFLOW_1)
        workflow1.add_steps([pool_step])

        workflow2 = Workflow(id=TestWorkflowIds.TEST_WORKFLOW_2)
        workflow2_step1 = create_test_send_message(
            step_factory,
            TestStepIds.STEP1,
            TestWorkflowIds.TEST_WORKFLOW_2,
            "Hi!",
        )
        workflow2_step2 = create_test_send_message(
            step_factory,
            TestStepIds.STEP2,
            TestWorkflowIds.TEST_WORKFLOW_2,
            "Hi!",
        )
        workflow2.add_steps([workflow2_step1, workflow2_step2])

        orchestrator.load([workflow1, workflow2])

        step_decision = create_test_pool_step(
            step_id=TestStepIds.WORKFLOW_DECISION,
            workflow_id=TestWorkflowIds.MAIN,
            question="Choice a workflow to follow",
            name="workflow decision",
            options=[
                ("workflow 1", TestWorkflowIds.TEST_WORKFLOW_1),
                ("workflow 2", TestWorkflowIds.TEST_WORKFLOW_2),
            ],
            is_decision=True,
        )

        orchestrator.add_step(step_decision)
        assert orchestrator.size() == 2

        orchestrator.start()
        assert orchestrator.state == WorkflowState.AWAITING_INPUT

        orchestrator.process("1")

        assert orchestrator.size() == 2
        assert orchestrator.state == WorkflowState.DEFAULT

    def test_clear_should_dont_duplicate_queue(
        self,
        step_factory: WorkflowStepFactory,
    ):
        mock_action_handler = Mock()
        mock_event_handler = Mock()
        orchestrator = WorkflowOrchestrator(
            action_handler=mock_action_handler,
            event_handler=mock_event_handler,
        )

        orchestrator.add_step(
            create_test_send_message(
                step_factory, TestStepIds.STEP1, TestWorkflowIds.MAIN, "Hi!"
            )
        )
        orchestrator.add_step(
            create_test_send_message(
                step_factory, TestStepIds.STEP2, TestWorkflowIds.MAIN, "Hi!"
            )
        )

        orchestrator.start()
        assert mock_action_handler.handle_send_message.call_count == 2

        orchestrator.start()
        assert mock_action_handler.handle_send_message.call_count == 4

        assert not orchestrator.is_started

    def test_with_decision_node_should_dont_copy_children_nodes_only_the_original_tree(
        self,
        step_factory: WorkflowStepFactory,
    ):
        mock_action_handler = Mock()
        mock_event_handler = Mock()
        orchestrator = WorkflowOrchestrator(
            action_handler=mock_action_handler,
            event_handler=mock_event_handler,
        )
        step_decision = create_test_pool_step(
            step_id=TestStepIds.WORKFLOW_DECISION,
            workflow_id=TestWorkflowIds.MAIN,
            question="Choice a workflow to follow",
            name="workflow decision",
            options=[
                ("workflow 1", TestWorkflowIds.TEST_WORKFLOW_1),
                ("workflow 2", TestWorkflowIds.TEST_WORKFLOW_2),
            ],
            is_decision=True,
        )

        workflow1 = Workflow(id=TestWorkflowIds.TEST_WORKFLOW_1)
        workflow1_step1 = create_test_send_message(
            step_factory,
            TestStepIds.STEP1,
            TestWorkflowIds.TEST_WORKFLOW_1,
            "Hi!",
        )
        workflow1.add_steps([workflow1_step1])

        workflow2 = Workflow(id=TestWorkflowIds.TEST_WORKFLOW_2)
        workflow2_step1 = create_test_send_message(
            step_factory,
            TestStepIds.STEP1,
            TestWorkflowIds.TEST_WORKFLOW_2,
            "Hi!",
        )
        workflow2.add_steps([workflow2_step1])

        orchestrator.add_step(step_decision)
        orchestrator.load([workflow1, workflow2])

        assert orchestrator.size() == 1

        orchestrator.start()

        assert orchestrator._action_handler.handle_send_pool.call_count == 1

        orchestrator.process("0")

        assert not orchestrator.is_started
        assert orchestrator.size() == 1

    def test_workflow_with_lazy_step(
        self,
        orchestrator: WorkflowOrchestrator,
    ):
        def mount_step(values: dict[str, str] | None = None) -> WorkflowStep:
            return (
                PoolBuilder()
                .with_id(TestStepIds.LAZY_POOL_STEP)
                .with_workflow_id(TestWorkflowIds.MAIN)
                .with_question("Choice a workflow to follow")
                .with_name("workflow decision")
                .with_option("opt1")
                .with_option("opt2")
                .build()
            )

        lazy_pool_step = (
            PoolBuilder()
            .lazy()
            .with_id(TestStepIds.LAZY_POOL_STEP)
            .with_workflow_id(TestWorkflowIds.MAIN)
            .with_question("Choice a workflow to follow")
            .with_name("workflow decision")
            .with_mount(data_loader=mount_step)
            .build()
        )

        orchestrator.add_step(lazy_pool_step)
        first_step = orchestrator.peek()
        assert first_step

        first_step.mount()
        assert len(first_step.options) == 2

import os
from enum import Enum
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agendabot.api.depedencies import (
    create_action_handler,
    create_event_handler,
)
from agendabot.modules.evolution_api.core import SecureMessageParser
from agendabot.modules.evolution_api.message_upsert_parser import (
    EvolutionApiMessageUpsertParser,
)
from agendabot.modules.evolution_api.schemas.message_upsert import (
    MessageUpsertData,
)
from agendabot.modules.workflow.orchestrator import WorkflowOrchestrator
from agendabot.modules.workflow.templates.mrfox import create_mrfox


class ConnectionStatus(Enum):
    OPEN = 1
    CLOSE = 2


class WppEvent(Enum):
    QRCODE_UPDATED = 1
    MESSAGES_UPSERT = 2
    SEND_MESSAGE = 3
    CONNECTION_UPDATE = 4
    APPLICATION_STARTUP = 5


map_wpp_event: dict[str, WppEvent] = {
    # "qrcode-updated": WppEvent.QRCODE_UPDATED,
    "messages-upsert": WppEvent.MESSAGES_UPSERT,
    # "send-message": WppEvent.SEND_MESSAGE,
    # "connection-update": WppEvent.CONNECTION_UPDATE,
    # "application-startup": WppEvent.APPLICATION_STARTUP
}

_ = load_dotenv()

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_DEFAULT_APP = os.getenv("EVOLUTION_DEFAULT_APP", "")
DEFAULT_TEST_NUMBER = "5584996792143"

app = FastAPI()

allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrators: dict[str, WorkflowOrchestrator] = {}


def get_or_create_orchestrator(phone_number: str) -> WorkflowOrchestrator:
    if phone_number not in _orchestrators:
        event_handler = create_event_handler(phone_number)
        action_handler = create_action_handler(phone_number)
        orchestrator = create_mrfox(event_handler, action_handler)
        _orchestrators[phone_number] = orchestrator

    orchestrator = _orchestrators[phone_number]
    if orchestrator.is_finished():
        del _orchestrators[phone_number]
        return get_or_create_orchestrator(phone_number)

    return orchestrator


def should_start_workflow(input: str) -> bool:
    input_lower = input.lower()
    return input_lower in ("#iniciar", "#agendar")


def should_finish_workflow(input: str) -> bool:
    input_lower = input.lower()
    return input_lower in ("#encerrar")


@app.get("/healthcheck")
def healthcheck():
    return {"status": "on"}


class EvolutionApiRequest(BaseModel):
    event: str
    instance: str
    data: dict[str, Any]
    destination: str
    date_time: str
    sender: str
    server_url: str
    apikey: str

    class Config:
        extra = "ignore"


@app.post("/api/wpp/webhook/{event}")
async def wpp_webhook(event: str, data: EvolutionApiRequest = Body(...)):
    wpp_event = map_wpp_event.get(event, None)
    request = EvolutionApiRequest.model_validate(data)

    if wpp_event == WppEvent.MESSAGES_UPSERT:
        secure_message_parser = SecureMessageParser[MessageUpsertData](
            EvolutionApiMessageUpsertParser()
        )

        parsed_data, errors = secure_message_parser.parse_and_validate(
            MessageUpsertData, request.data
        )

        if len(errors) > 0:
            print(errors)
            return

        assert parsed_data, "Parsed data should not be None"
        print(parsed_data.message)

        phone_number = parsed_data.client_phone
        message = parsed_data.message

        orchestrator = get_or_create_orchestrator(phone_number)

        if should_finish_workflow(message):
            del _orchestrators[phone_number]
            return

        if not orchestrator.is_started and should_start_workflow(message):
            await orchestrator.start()
            return

        if orchestrator.is_finished():
            return

        if orchestrator.is_started:
            await orchestrator.process(message)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

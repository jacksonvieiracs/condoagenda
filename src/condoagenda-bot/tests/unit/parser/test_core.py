from typing import Any, Dict

from pydantic import BaseModel

from agendabot.modules.evolution_api.core import (
    BaseMessageParser,
    SecureMessageParser,
)


class SimpleMessage(BaseModel):
    message: str


class SimpleMessageParser(BaseMessageParser):
    def define_mappings(self) -> Dict[str, Dict[str, Any]]:
        return {
            "message": {
                "path": ["message"],
            },
        }


class TestSecureMessageParser:
    def test_parse_and_validate(self):
        parser = SecureMessageParser[SimpleMessage](SimpleMessageParser())
        data = {
            "message": "Hello, world!",
        }

        data, errors = parser.parse_and_validate(SimpleMessage, data)

        assert len(errors) == 0
        assert isinstance(data, SimpleMessage)
        assert data.message == "Hello, world!"

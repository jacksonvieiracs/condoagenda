from agendabot.modules.evolution_api.message_upsert_parser import (
    EvolutionApiMessageUpsertParser,
)


class TestEvolutionApiMessageUpsertParser:
    parser = EvolutionApiMessageUpsertParser()

    def test_provider_name(self):
        assert self.parser.provider_name == "evolution_api"

    def test_parse(self):
        data = {
            "pushName": "Jhon Doe",
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
            },
            "message": {
                "conversation": "Hello, how are you?",
            },
            "messageTimestamp": 1714732800,
        }

        result = self.parser.parse(data)
        assert result.is_valid()
        assert result.data == {
            "client_name": "Jhon Doe",
            "client_phone": "5511999999999",
            "message": "Hello, how are you?",
            "message_timespamp": 1714732800,
        }

    def test_parse_with_error(self):
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
            },
        }
        result = self.parser.parse(data)
        assert not result.is_valid()

        count_missing_keys = len(
            [error for error in result.errors if error.error_type == "KeyError"]
        )

        assert count_missing_keys == 3

from typing import Any, Dict

from .core import BaseMessageParser


class EvolutionApiMessageUpsertParser(BaseMessageParser):
    provider_name = "evolution_api"

    def define_mappings(self) -> Dict[str, Dict[str, Any]]:
        return {
            "client_name": {
                "path": ["pushName"],
            },
            "client_phone": {
                "path": ["key", "remoteJid"],
                "transformer": self._extract_phone,
            },
            "message": {
                "path": ["message", "conversation"],
            },
            "message_timespamp": {
                "path": ["messageTimestamp"],
                "transformer": int,
            },
        }

    def _extract_phone(self, remote_jid: str) -> str:
        """Extract phone from remoteJid format: '5511999999999@s.whatsapp.net'"""
        return remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

    def _map_sender(self, from_me: bool) -> str:
        return "assistant" if from_me else "user"

    def _timestamp_to_datetime(self, timestamp: int) -> str:
        from datetime import datetime

        return datetime.fromtimestamp(timestamp).isoformat()

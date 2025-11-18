from enum import Enum

import httpx


class ConnectionStatus(Enum):
    OPEN = 1
    CLOSE = 2


class SendPlainTextMessageResponse:
    def __init__(self, ok: bool, message: str) -> None:
        self.ok = ok
        self.message = message


class GetConnectionStatusResponse:
    def __init__(self, status: ConnectionStatus) -> None:
        self.status = status


class GetQRCodeResponse:
    def __init__(self, ok: bool, message: str, qr_code: str) -> None:
        self.ok = ok
        self.message = message
        self.qr_code = qr_code


class WhatsAppClient:
    def __init__(self, base_url: str, api_key: str, default_instance: str):
        self._client = httpx.AsyncClient(base_url=base_url)
        self._client.headers = {
            "apiKey": api_key,
            "Content-type": "application/json",
        }
        self._default_instance = default_instance

    async def send_plain_text_message(
        self, message: str, phone_number: str
    ) -> SendPlainTextMessageResponse:
        data = {"text": message, "number": phone_number}

        # handle timeout exceptions returning a error to the client
        response = await self._client.post(
            f"/message/sendText/{self._default_instance}", json=data, timeout=2
        )

        if response.is_error:
            return SendPlainTextMessageResponse(
                ok=False, message="Erro try sending message again!"
            )

        return SendPlainTextMessageResponse(ok=True, message="Success!")

    async def get_connection_status(self) -> GetConnectionStatusResponse:
        response = await self._client.get(
            f"/instance/connectionState/{self._default_instance}"
        )
        data = response.json()
        status = (
            ConnectionStatus.OPEN
            if data["status"] == "open"
            else ConnectionStatus.CLOSE
        )
        return GetConnectionStatusResponse(status=status)

    async def connect(self):
        await self._client.post(f"/instance/connectionState/{self._default_instance}")

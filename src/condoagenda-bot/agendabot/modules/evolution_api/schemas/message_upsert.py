from pydantic import BaseModel


class MessageUpsertData(BaseModel):
    client_name: str
    client_phone: str
    message: str
    message_timespamp: int

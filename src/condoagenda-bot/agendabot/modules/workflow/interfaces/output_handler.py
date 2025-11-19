from abc import ABC, abstractmethod


class IOutputHandler(ABC):
    @abstractmethod
    async def send_message(self, message: str): ...

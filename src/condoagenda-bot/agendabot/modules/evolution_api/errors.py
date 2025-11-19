from dataclasses import dataclass
from typing import Any


@dataclass
class ParserError:
    field: str
    expected_path: str
    error_type: str
    details: str
    raw_value: Any = None

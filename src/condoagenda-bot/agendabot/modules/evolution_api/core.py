from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from .errors import ParserError

T = TypeVar("T", bound=BaseModel)


class ParseResult:
    """Holds both success and failure states with detailed context"""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.errors: list[ParserError] = []

    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(
        self,
        field: str,
        path: str,
        error_type: str,
        details: str,
        raw_value: Any = None,
    ):
        self.errors.append(
            ParserError(field, path, error_type, details, raw_value)
        )

    def set_field(self, field: str, value: Any):
        self.data[field] = value


class BaseMessageParser(ABC):
    provider_name: str = "unknown"

    def parse(self, raw_data: Dict[str, Any]) -> ParseResult:
        result = ParseResult()

        mappings = self.define_mappings()

        for target_field, config in mappings.items():
            self._extract_field(
                result=result,
                data=raw_data,
                target_field=target_field,
                path=config["path"],
                transformer=config.get("transformer"),
            )

        return result

    @abstractmethod
    def define_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Define how to extract each field from raw data.

        Returns:
            Dict with structure:
            {
                'target_field_name': {
                    'path': ['nested', 'keys', 'to', 'value'],
                    'transformer': optional_function  # Optional
                }
            }
        """
        pass

    def _extract_field(
        self,
        result: ParseResult,
        data: dict[str, Any],
        target_field: str,
        path: list[str],
        transformer: Callable[[str | int], str] | None = None,
    ):
        """Safely extract and transform field with detailed error tracking"""
        try:
            value = data
            for key in path:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    raise KeyError(
                        f"Expected dict at '{key}', got {type(value).__name__}"
                    )

                if value is None:
                    raise KeyError(f"Missing key: '{key}'")

            if transformer:
                assert isinstance(value, str) or isinstance(value, int)
                value = transformer(value)

            result.set_field(target_field, value)

        except (KeyError, ValueError, TypeError) as e:
            result.add_error(
                field=target_field,
                path=" -> ".join(path),
                error_type=type(e).__name__,
                details=str(e),
                raw_value=data,
            )


class SecureMessageParser(Generic[T]):
    """Generic parser that coordinates provider-specific parsing and validation"""

    def __init__(self, parser: BaseMessageParser):
        self.parser = parser

    def parse_and_validate(
        self, model: type[T], raw_data: dict[str, str]
    ) -> tuple[T | None, list[ParserError]]:
        """
        parsing:
        1. Provider-specific parsing with detailed error tracking
        2. Pydantic validation

        Returns: (parsed_data, errors)
        """
        parse_result = self.parser.parse(raw_data)

        if not parse_result.is_valid():
            return None, parse_result.errors

        try:
            validated = model.model_validate(parse_result.data)
            return validated, []
        except ValidationError as e:
            errors = []
            for err in e.errors():
                field = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    ParserError(
                        field=field,
                        expected_path=f"validated.{field}",
                        error_type="validation_error",
                        details=err["msg"],
                        raw_value=parse_result.data.get(field),
                    )
                )
            return None, errors

from pydantic.dataclasses import dataclass


@dataclass
class ErrorResponse:
    details: str

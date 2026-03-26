from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCatalogEntry:
    status_code: int
    error_code: str

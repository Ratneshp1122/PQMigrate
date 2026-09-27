"""Offline validation against pinned official interchange schemas."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft4Validator, Draft7Validator


class ExportValidationError(ValueError):
    """Raised when an exported document does not satisfy its standard schema."""


_SCHEMAS = {
    "sarif": ("sarif-schema-2.1.0.json", Draft4Validator),
    "cbom": ("bom-1.7.schema.json", Draft7Validator),
}


def validate_export(document: dict[str, Any], export_format: str) -> None:
    """Validate *document* against the vendored schema for *export_format*."""
    normalized = export_format.lower()
    if normalized not in _SCHEMAS:
        raise ValueError(f"Unsupported export format: {export_format}")

    schema_name, validator_type = _SCHEMAS[normalized]
    schema_path = Path(__file__).with_name("schemas") / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(validator_type(schema).iter_errors(document), key=lambda error: list(error.path))
    if not errors:
        return

    error = errors[0]
    location = ".".join(str(part) for part in error.absolute_path) or "<document>"
    raise ExportValidationError(
        f"{normalized.upper()} schema validation failed at {location}: {error.message}"
    )

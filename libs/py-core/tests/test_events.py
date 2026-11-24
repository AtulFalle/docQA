from uuid import uuid4

import pytest
from pydantic import ValidationError

from docqa_core.events import DocumentIngestRequested

WIRE = {
    "eventId": str(uuid4()),
    "occurredAt": "2026-11-24T10:00:00Z",
    "tenantId": str(uuid4()),
    "documentId": str(uuid4()),
    "documentVersionId": str(uuid4()),
}


def test_parses_camel_case_wire_format_into_snake_case_fields() -> None:
    event = DocumentIngestRequested.model_validate(WIRE)
    assert str(event.document_version_id) == WIRE["documentVersionId"]
    assert event.model_dump(mode="json", by_alias=True) == WIRE


def test_rejects_unknown_fields_and_naive_timestamps() -> None:
    with pytest.raises(ValidationError):
        DocumentIngestRequested.model_validate({**WIRE, "extra": 1})
    with pytest.raises(ValidationError):
        DocumentIngestRequested.model_validate({**WIRE, "occurredAt": "2026-11-24T10:00:00"})

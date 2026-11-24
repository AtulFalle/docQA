import pytest
from temporalio.testing import ActivityEnvironment

from docqa_workers.activities.ingest import ALL_ACTIVITIES, IngestInput

INPUT = IngestInput(tenant_id="t1", document_id="d1", document_version_id="v1")
STAGES = ["validate_document", "extract_document", "chunk_document", "embed_chunks", "index_chunks"]


@pytest.mark.parametrize(("activity_fn", "stage"), list(zip(ALL_ACTIVITIES, STAGES, strict=True)))
async def test_activity_returns_stage_name(activity_fn, stage: str) -> None:  # type: ignore[no-untyped-def]
    assert await ActivityEnvironment().run(activity_fn, INPUT) == stage

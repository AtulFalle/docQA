import uuid

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from docqa_workers.activities.ingest import ALL_ACTIVITIES, IngestInput
from docqa_workers.workflows.ingest import IngestDocumentWorkflow

STAGES = ["validate_document", "extract_document", "chunk_document", "embed_chunks", "index_chunks"]

pytestmark = pytest.mark.integration


async def test_ingest_workflow_runs_all_stages() -> None:
    async with (
        await WorkflowEnvironment.start_time_skipping() as env,
        Worker(
            env.client,
            task_queue="test-ingestion",
            workflows=[IngestDocumentWorkflow],
            activities=ALL_ACTIVITIES,
        ),
    ):
        result = await env.client.execute_workflow(
            IngestDocumentWorkflow.run,
            IngestInput(tenant_id="t1", document_id="d1", document_version_id="v1"),
            id=f"ingest-{uuid.uuid4().hex}",
            task_queue="test-ingestion",
        )
    assert result.document_version_id == "v1"
    assert result.stages_completed == STAGES

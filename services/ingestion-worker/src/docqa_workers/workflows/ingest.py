"""Document ingestion workflow."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from docqa_workers.activities.ingest import (
        IngestInput,
        IngestResult,
        chunk_document,
        embed_chunks,
        extract_document,
        index_chunks,
        validate_document,
    )

__all__ = ["IngestDocumentWorkflow", "IngestInput", "IngestResult"]

RETRY_POLICY = RetryPolicy(
    maximum_attempts=5,
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    non_retryable_error_types=["ValidationError"],
)


@workflow.defn
class IngestDocumentWorkflow:
    """Runs the ingestion stages sequentially with retries."""

    @workflow.run
    async def run(self, params: IngestInput) -> IngestResult:
        """Execute every ingestion stage and report those completed."""
        completed: list[str] = []
        for activity_fn in (
            validate_document,
            extract_document,
            chunk_document,
            embed_chunks,
            index_chunks,
        ):
            stage: str = await workflow.execute_activity(
                activity_fn,
                params,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RETRY_POLICY,
            )
            completed.append(stage)
        return IngestResult(
            document_version_id=params.document_version_id, stages_completed=completed
        )

"""Ingestion activities (stubs)."""

from dataclasses import dataclass

from temporalio import activity

from docqa_core.logging import get_logger

log = get_logger(__name__)


@dataclass
class IngestInput:
    """Identifies the document version an activity operates on."""

    tenant_id: str
    document_id: str
    document_version_id: str


@dataclass
class IngestResult:
    """Outcome of a workflow run."""

    document_version_id: str
    stages_completed: list[str]


def _log_stage(stage: str, params: IngestInput) -> str:
    log.info(
        "ingest.stage",
        stage=stage,
        tenant_id=params.tenant_id,
        document_id=params.document_id,
        document_version_id=params.document_version_id,
    )
    return stage


@activity.defn
async def validate_document(params: IngestInput) -> str:
    """Validate the raw object (stub).

    Returns:
        The stage name.
    """
    # TODO(M1): verify object exists, size/mime limits, malware scan, dedupe by content hash.
    return _log_stage("validate_document", params)


@activity.defn
async def extract_document(params: IngestInput) -> str:
    """Extract structured text (stub).

    Returns:
        The stage name.
    """
    # TODO(M1): parse the raw object into structured text/layout (OCR fallback).
    return _log_stage("extract_document", params)


@activity.defn
async def chunk_document(params: IngestInput) -> str:
    """Split the document into chunks (stub).

    Returns:
        The stage name.
    """
    # TODO(M1): hierarchical chunking with section paths and page ranges.
    return _log_stage("chunk_document", params)


@activity.defn
async def embed_chunks(params: IngestInput) -> str:
    """Embed chunks (stub).

    Returns:
        The stage name.
    """
    # TODO(M1): batch-embed chunks with the configured embedding model.
    return _log_stage("embed_chunks", params)


@activity.defn
async def index_chunks(params: IngestInput) -> str:
    """Index chunks and vectors (stub).

    Returns:
        The stage name.
    """
    # TODO(M1): upsert vectors to Qdrant and chunks to Postgres; mark version ready.
    return _log_stage("index_chunks", params)


ALL_ACTIVITIES = [validate_document, extract_document, chunk_document, embed_chunks, index_chunks]

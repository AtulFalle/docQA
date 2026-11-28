"""Provider interfaces and their registries, one registry per interface.

Implementations register themselves with ``@<registry>.register("name")``. The built-in fakes
live in ``docqa_core.providers.fakes``; the composition root imports that module (and any
``plugins`` from settings) and then builds each provider from ``settings.providers``.
"""

from docqa_core.providers.ingestion import Chunker, Parser, chunkers, parsers
from docqa_core.providers.llm import LLMProvider, llms
from docqa_core.providers.retrieval import (
    Embedder,
    Reranker,
    VectorStore,
    embedders,
    rerankers,
    vector_stores,
)

__all__ = [
    "Chunker",
    "Embedder",
    "LLMProvider",
    "Parser",
    "Reranker",
    "VectorStore",
    "chunkers",
    "embedders",
    "llms",
    "parsers",
    "rerankers",
    "vector_stores",
]

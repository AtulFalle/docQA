"""Built-in fake providers. Importing this package registers all of them under ``"fake"``.

The fakes are deterministic and need no infrastructure, so the whole pipeline runs in tests
and in compose without any model or database (M1).
"""

from docqa_core.providers.fakes.ingestion import ParagraphChunker, PlainTextParser
from docqa_core.providers.fakes.llm import FakeLLM
from docqa_core.providers.fakes.retrieval import FakeEmbedder, InMemoryVectorStore, LexicalReranker

__all__ = [
    "FakeEmbedder",
    "FakeLLM",
    "InMemoryVectorStore",
    "LexicalReranker",
    "ParagraphChunker",
    "PlainTextParser",
]

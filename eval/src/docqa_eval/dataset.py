"""Loading, validating and summarising golden datasets and corpus manifests."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from docqa_eval.schema import GoldenItem

# Group memberships of the synthetic seed users referenced by the shipped golden set.
SEED_USER_GROUPS: Final[dict[str, frozenset[str]]] = {
    "u_hr_1": frozenset({"hr", "all"}),
    "u_legal_1": frozenset({"legal", "all"}),
    "u_eng_1": frozenset({"all"}),
}


class ManifestEntry(BaseModel):
    """Per-document metadata from ``manifest.json``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str = Field(min_length=1)
    acl_groups: list[str]
    title: str


_MANIFEST_ADAPTER: Final[TypeAdapter[dict[str, ManifestEntry]]] = TypeAdapter(
    dict[str, ManifestEntry]
)


def load_golden(path: Path) -> list[GoldenItem]:
    """Parse a JSONL golden file; errors name the offending line number."""
    items: list[GoldenItem] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                items.append(GoldenItem.model_validate_json(line))
            except ValidationError as exc:
                raise ValueError(f"{path}:{lineno}: {exc}") from exc
    return items


def load_manifest(path: Path) -> dict[str, ManifestEntry]:
    """Parse a corpus manifest mapping doc_id to tenant, ACL groups and title."""
    return _MANIFEST_ADAPTER.validate_json(path.read_bytes())


def can_read(entry: ManifestEntry, groups: Collection[str]) -> bool:
    """True if any of the user's groups is allowed to read the document."""
    return not set(entry.acl_groups).isdisjoint(groups)


def validate_dataset(items: Sequence[GoldenItem], corpus_doc_ids: set[str] | None) -> list[str]:
    """Return human-readable problems: duplicate ids and, if known, unknown gold doc ids."""
    errors: list[str] = []
    counts = Counter(item.id for item in items)
    for item_id, n in sorted(counts.items()):
        if n > 1:
            errors.append(f"duplicate id {item_id!r} ({n} occurrences)")
    if corpus_doc_ids is not None:
        errors.extend(
            f"{item.id}: unknown doc_id {evidence.doc_id!r}"
            for item in items
            for evidence in item.gold
            if evidence.doc_id not in corpus_doc_ids
        )
    return errors


def validate_tenants(
    items: Sequence[GoldenItem], manifest: Mapping[str, ManifestEntry]
) -> list[str]:
    """Return errors where an item's tenant differs from the tenant of a document it cites."""
    errors: list[str] = []
    for item in items:
        for evidence in item.gold:
            entry = manifest.get(evidence.doc_id)
            if entry is not None and entry.tenant_id != item.tenant_id:
                errors.append(
                    f"{item.id}: tenant {item.tenant_id!r} cites {evidence.doc_id!r} "
                    f"which belongs to tenant {entry.tenant_id!r}"
                )
    return errors


def dataset_stats(items: Sequence[GoldenItem]) -> dict[str, object]:
    """Counts by question type, expected behaviour, asking user and tag, plus cited docs."""
    return {
        "total": len(items),
        "by_question_type": dict(sorted(Counter(i.question_type for i in items).items())),
        "by_expected_behavior": dict(sorted(Counter(i.expected_behavior for i in items).items())),
        "by_asking_user": dict(sorted(Counter(i.asking_user for i in items).items())),
        "by_tag": dict(sorted(Counter(t for i in items for t in i.tags).items())),
        "gold_docs": sorted({ev.doc_id for i in items for ev in i.gold}),
    }

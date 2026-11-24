"""Checks on the shipped golden_v0 set against the sample corpus manifest."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

import pytest

from docqa_eval.dataset import (
    SEED_USER_GROUPS,
    can_read,
    dataset_stats,
    load_golden,
    load_manifest,
    validate_dataset,
    validate_tenants,
)
from docqa_eval.schema import QuestionType

EVAL_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = EVAL_ROOT / "datasets" / "golden_v0.jsonl"
CORPUS_DIR = EVAL_ROOT / "corpus" / "sample"


def test_shipped_golden_loads_25_items() -> None:
    items = load_golden(GOLDEN_PATH)
    assert len(items) == 25


def test_shipped_golden_validates_against_manifest() -> None:
    manifest = load_manifest(CORPUS_DIR / "manifest.json")
    items = load_golden(GOLDEN_PATH)
    assert validate_dataset(items, set(manifest)) == []
    assert validate_tenants(items, manifest) == []


def test_every_question_type_is_present_at_least_three_times() -> None:
    items = load_golden(GOLDEN_PATH)
    stats = dataset_stats(items)
    by_type = stats["by_question_type"]
    assert isinstance(by_type, dict)
    for question_type in get_args(QuestionType):
        assert by_type.get(question_type, 0) >= 3, question_type


def test_acl_trap_askers_lack_access_per_manifest() -> None:
    manifest = load_manifest(CORPUS_DIR / "manifest.json")
    items = load_golden(GOLDEN_PATH)
    acl_items = [i for i in items if i.question_type == "acl_trap"]
    assert acl_items
    for item in acl_items:
        acl_tags = [t for t in item.tags if t.startswith("acl:")]
        assert acl_tags, item.id
        user_groups = SEED_USER_GROUPS[item.asking_user]
        for tag in acl_tags:
            doc_id = tag.removeprefix("acl:")
            assert not can_read(manifest[doc_id], user_groups), (item.id, doc_id)


def test_injection_item_is_tagged() -> None:
    items = load_golden(GOLDEN_PATH)
    assert [i.id for i in items if "injection" in i.tags] == ["v0-agg-04"]


def test_load_golden_reports_line_number(tmp_path: Path) -> None:
    bad = tmp_path / "bad.jsonl"
    good_line = (
        '{"id": "a", "tenant_id": "t", "asking_user": "u", "question": "q", '
        '"question_type": "factual", "expected_behavior": "abstain"}'
    )
    bad.write_text(f"{good_line}\n\n{{not json}}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.jsonl:3:"):
        load_golden(bad)


def test_validate_dataset_flags_duplicates_and_unknown_docs() -> None:
    items = load_golden(GOLDEN_PATH)
    errors = validate_dataset([*items, items[0]], {"policy_leave"})
    assert any("duplicate id 'v0-fact-01'" in e for e in errors)
    assert any("unknown doc_id 'resume_priya_sharma'" in e for e in errors)

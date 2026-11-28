"""Value sets must agree in three places: Python StrEnums, @docqa/contracts and DB CHECKs.

The contracts comparison is a unit test (it reads the TypeScript sources). The CHECK
comparison runs against a database migrated by Prisma (DOCQA_TEST_DATABASE_URL).
"""

import enum
import os
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from docqa_core.db import models

CONTRACTS = Path(__file__).resolve().parents[3] / "libs/shared/contracts/src/lib"

# @docqa/contracts const -> (file, Python enum)
CONTRACT_SETS: dict[str, tuple[str, type[enum.StrEnum]]] = {
    "TENANT_STATUSES": ("tenants/tenant.models.ts", models.TenantStatus),
    "DOCUMENT_STATUSES": ("documents/document.models.ts", models.DocumentStatus),
    "VERSION_STATUSES": ("documents/document.models.ts", models.VersionStatus),
    "REJECTION_REASONS": ("documents/document.models.ts", models.RejectionReason),
    "UPLOAD_STATUSES": ("documents/document.models.ts", models.UploadStatus),
    "JOB_KINDS": ("jobs/job.models.ts", models.JobKind),
    "JOB_STATUSES": ("jobs/job.models.ts", models.JobStatus),
    "PRINCIPAL_TYPES": ("access/access.models.ts", models.PrincipalType),
    "PERMISSIONS": ("access/access.models.ts", models.Permission),
    "USER_ROLES": ("access/access.models.ts", models.UserRole),
    "MEMBERSHIP_SOURCES": ("access/access.models.ts", models.MembershipSource),
}

# CHECK constraint -> Python enum
CHECKS: dict[str, type[enum.StrEnum]] = {
    "ck_tenants_status": models.TenantStatus,
    "ck_search_indexes_status": models.SearchIndexStatus,
    "ck_search_indexes_distance": models.Distance,
    "ck_model_prices_kind": models.UsageKind,
    "ck_users_role": models.UserRole,
    "ck_groups_source": models.MembershipSource,
    "ck_group_memberships_source": models.MembershipSource,
    "ck_document_acls_principal_type": models.PrincipalType,
    "ck_document_acls_permission": models.Permission,
    "ck_documents_status": models.DocumentStatus,
    "ck_document_versions_status": models.VersionStatus,
    "ck_document_versions_rejection_reason": models.RejectionReason,
    "ck_upload_sessions_status": models.UploadStatus,
    "ck_document_version_indexes_status": models.IndexEntryStatus,
    "ck_jobs_kind": models.JobKind,
    "ck_jobs_status": models.JobStatus,
    "ck_queries_source": models.QuerySource,
    "ck_queries_status": models.QueryStatus,
    "ck_feedback_rating": models.FeedbackRating,
    "ck_usage_events_kind": models.UsageKind,
    "ck_usage_events_source": models.UsageSource,
    "ck_usage_daily_kind": models.UsageKind,
    "ck_usage_daily_source": models.UsageSource,
    "ck_audit_log_actor_type": models.ActorType,
    "ck_audit_log_outcome": models.AuditOutcome,
}


def _ts_const(source: str, name: str) -> list[str]:
    match = re.search(rf"export const {name} = \[(.*?)\] as const", source, re.DOTALL)
    assert match, f"{name} not found in contracts"
    return re.findall(r"'([a-z_]+)'", match.group(1))


@pytest.mark.parametrize("const_name", sorted(CONTRACT_SETS))
def test_contract_value_set_matches_python_enum(const_name: str) -> None:
    file, py_enum = CONTRACT_SETS[const_name]
    values = _ts_const((CONTRACTS / file).read_text(encoding="utf-8"), const_name)
    assert values == [m.value for m in py_enum], const_name


TEST_URL = os.environ.get("DOCQA_TEST_DATABASE_URL")


@pytest.mark.integration
@pytest.mark.skipif(not TEST_URL, reason="DOCQA_TEST_DATABASE_URL not set")
def test_check_constraints_match_python_enums() -> None:
    assert TEST_URL
    engine = create_engine(TEST_URL)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE contype = 'c' AND conname = ANY(:names)"
                ),
                {"names": list(CHECKS)},
            ).all()
    finally:
        engine.dispose()
    found = {name: set(re.findall(r"'([a-z_]+)'::", definition)) for name, definition in rows}
    assert set(found) == set(CHECKS), "missing CHECK constraints"
    problems = [
        f"{name}: db={sorted(found[name])} python={sorted(m.value for m in py_enum)}"
        for name, py_enum in CHECKS.items()
        if found[name] != {m.value for m in py_enum}
    ]
    assert not problems, "\n".join(problems)


def test_db_enum_module_re_exports_the_shared_value_sets():
    from docqa_core import value_sets
    from docqa_core.db.models import enums

    assert enums.__all__ == sorted(enums.__all__)
    for name in enums.__all__:
        assert getattr(enums, name) is getattr(value_sets, name)
    shared = {name for name, obj in vars(value_sets).items() if isinstance(obj, enum.EnumType)}
    assert shared == set(enums.__all__)

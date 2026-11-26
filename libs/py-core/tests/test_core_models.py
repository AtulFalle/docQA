from sqlalchemy import UniqueConstraint

from docqa_core.db import GLOBAL_TABLES, TENANT_SCOPED_TABLES, Base

EXPECTED_TABLES = {
    "tenants",
    "tenant_settings",
    "search_indexes",
    "model_prices",
    "users",
    "groups",
    "group_memberships",
    "document_acls",
    "documents",
    "document_versions",
    "upload_sessions",
    "chunks",
    "document_version_indexes",
    "jobs",
    "conversations",
    "queries",
    "answers",
    "citations",
    "feedback",
    "usage_events",
    "usage_daily",
    "audit_log",
}


def test_table_set() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_table_is_classified() -> None:
    classified = set(TENANT_SCOPED_TABLES) | set(GLOBAL_TABLES) | {"audit_log"}
    assert classified == EXPECTED_TABLES


def test_tenant_scoped_tables_have_non_null_tenant_id() -> None:
    for name in TENANT_SCOPED_TABLES:
        col = Base.metadata.tables[name].c.get("tenant_id")
        assert col is not None, name
        assert not col.nullable, name


def test_tenant_tables_with_own_id_are_unique_on_tenant_and_id() -> None:
    for name in TENANT_SCOPED_TABLES:
        table = Base.metadata.tables[name]
        if "id" not in table.c or name == "usage_events":
            continue
        unique_sets = {
            tuple(c.name for c in con.columns)
            for con in table.constraints
            if isinstance(con, UniqueConstraint)
        }
        assert ("tenant_id", "id") in unique_sets, name


def test_composite_tenant_foreign_keys() -> None:
    fks = {fk.name: fk for fk in Base.metadata.tables["chunks"].foreign_key_constraints}
    fk = fks["fk_chunks_document_version_id_document_versions"]
    assert [c.name for c in fk.columns] == ["tenant_id", "document_version_id"]


def test_partitioned_tables_include_partition_key_in_primary_key() -> None:
    usage_pk = [c.name for c in Base.metadata.tables["usage_events"].primary_key]
    audit_pk = [c.name for c in Base.metadata.tables["audit_log"].primary_key]
    assert usage_pk == ["id", "occurred_at"]
    assert audit_pk == ["id", "created_at"]


def test_chunk_metadata_column_name() -> None:
    assert "metadata" in Base.metadata.tables["chunks"].c


def test_naming_convention_applied() -> None:
    assert Base.metadata.tables["tenants"].primary_key.name == "pk_tenants"
    uniques = {c.name for c in Base.metadata.tables["users"].constraints}
    assert "uq_users_tenant_id_idp_issuer_external_subject" in uniques

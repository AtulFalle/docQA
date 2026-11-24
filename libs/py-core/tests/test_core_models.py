from docqa_core.db import TENANT_SCOPED_TABLES, Base

EXPECTED_TABLES = {
    "tenants",
    "users",
    "groups",
    "group_memberships",
    "documents",
    "document_acls",
    "document_versions",
    "chunks",
    "jobs",
    "audit_log",
}


def test_table_set() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_tenant_scoped_tables_have_tenant_id() -> None:
    scoped = set(Base.metadata.tables) - {"tenants", "audit_log"}
    assert scoped == set(TENANT_SCOPED_TABLES)
    for name in scoped:
        col = Base.metadata.tables[name].c.get("tenant_id")
        assert col is not None, name
        assert not col.nullable, name


def test_chunks_reference_document_version() -> None:
    assert "document_version_id" in Base.metadata.tables["chunks"].c


def test_chunk_metadata_column_name() -> None:
    assert "metadata" in Base.metadata.tables["chunks"].c


def test_naming_convention_applied() -> None:
    assert Base.metadata.tables["tenants"].primary_key.name == "pk_tenants"
    fk_names = {fk.name for fk in Base.metadata.tables["documents"].foreign_key_constraints}
    assert "fk_documents_current_version_id_document_versions" in fk_names

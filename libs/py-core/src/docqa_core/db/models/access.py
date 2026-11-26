"""Identity and access tables (RLS)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from docqa_core.db.base import Base, TimestampMixin
from docqa_core.db.models._columns import (
    created_ts,
    enum_type,
    opt_ts,
    tenant_fk,
    tenant_ref,
    uuid_pk,
)
from docqa_core.db.models.enums import MembershipSource, Permission, PrincipalType, UserRole


class User(TimestampMixin, Base):
    """A tenant member, identified by IdP issuer and subject. Never hard-deleted."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "idp_issuer", "external_subject"),
        Index("ix_users_tenant_id_email", "tenant_id", "email"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    idp_issuer: Mapped[str] = mapped_column(sa.String(255))
    external_subject: Mapped[str] = mapped_column(sa.String(255))
    email: Mapped[str | None] = mapped_column(sa.String(320))
    display_name: Mapped[str | None] = mapped_column(sa.String(255))
    role: Mapped[UserRole] = mapped_column(
        enum_type(UserRole, "user_role"), server_default=UserRole.MEMBER.value
    )
    last_login_at: Mapped[datetime | None] = opt_ts()
    deactivated_at: Mapped[datetime | None] = opt_ts()
    erased_at: Mapped[datetime | None] = opt_ts()


class Group(TimestampMixin, Base):
    """A flat set of users within a tenant."""

    __tablename__ = "groups"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "name"),
        UniqueConstraint("tenant_id", "external_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    name: Mapped[str] = mapped_column(sa.String(255))
    source: Mapped[MembershipSource] = mapped_column(
        enum_type(MembershipSource, "membership_source"),
        server_default=MembershipSource.LOCAL.value,
    )
    external_id: Mapped[str | None] = mapped_column(sa.String(255))


class GroupMembership(Base):
    """A user in a group. IdP memberships are replaced at each login."""

    __tablename__ = "group_memberships"
    __table_args__ = (
        tenant_ref(
            "group_id", "groups", "fk_group_memberships_group_id_groups", ondelete="CASCADE"
        ),
        tenant_ref("user_id", "users", "fk_group_memberships_user_id_users", ondelete="CASCADE"),
        Index("ix_group_memberships_tenant_id_user_id", "tenant_id", "user_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    group_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    source: Mapped[MembershipSource] = mapped_column(
        enum_type(MembershipSource, "membership_source"),
        server_default=MembershipSource.LOCAL.value,
    )
    created_at: Mapped[datetime] = created_ts()


class DocumentAcl(TimestampMixin, Base):
    """One grant per principal per document. Allow-only."""

    __tablename__ = "document_acls"
    __table_args__ = (
        tenant_ref(
            "document_id", "documents", "fk_document_acls_document_id_documents", ondelete="CASCADE"
        ),
        tenant_ref("user_id", "users", "fk_document_acls_user_id_users", ondelete="CASCADE"),
        tenant_ref("group_id", "groups", "fk_document_acls_group_id_groups", ondelete="CASCADE"),
        tenant_ref("granted_by", "users", "fk_document_acls_granted_by_users"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "document_id", "user_id"),
        UniqueConstraint("tenant_id", "document_id", "group_id"),
        Index("ix_document_acls_tenant_id_user_id", "tenant_id", "user_id"),
        Index("ix_document_acls_tenant_id_group_id", "tenant_id", "group_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    document_id: Mapped[uuid.UUID]
    principal_type: Mapped[PrincipalType] = mapped_column(
        enum_type(PrincipalType, "principal_type")
    )
    user_id: Mapped[uuid.UUID | None]
    group_id: Mapped[uuid.UUID | None]
    permission: Mapped[Permission] = mapped_column(enum_type(Permission, "permission"))
    granted_by: Mapped[uuid.UUID | None]

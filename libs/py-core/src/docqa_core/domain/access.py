"""Who is asking: the principal and its principal set (ADR 0006, section 5).

The principal set is what search filters on. Every vector point carries ``acl_principals``,
and a principal may see a chunk when the two sets share at least one entry:

- ``t``: granted to the whole tenant
- ``u:<user id>``: granted to one user
- ``g:<group id>``: granted to one group

Tenant admins see every document in their tenant.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from uuid import UUID

from docqa_core.value_sets import UserRole

TENANT_PRINCIPAL = "t"


def user_principal(user_id: UUID) -> str:
    """Return the principal-set entry for one user."""
    return f"u:{user_id}"


def group_principal(group_id: UUID) -> str:
    """Return the principal-set entry for one group."""
    return f"g:{group_id}"


@dataclass(frozen=True, slots=True)
class Principal:
    """An authenticated user acting inside one tenant."""

    tenant_id: UUID
    user_id: UUID
    group_ids: frozenset[UUID] = field(default_factory=frozenset)
    role: UserRole = UserRole.MEMBER

    @property
    def is_tenant_admin(self) -> bool:
        """Whether the principal sees every document in the tenant."""
        return self.role is UserRole.ADMIN

    def acl_principals(self) -> tuple[str, ...]:
        """Return the principal set in a stable order: tenant, user, then sorted groups."""
        groups = sorted(group_principal(group_id) for group_id in self.group_ids)
        return (TENANT_PRINCIPAL, user_principal(self.user_id), *groups)

    def can_access(self, *, tenant_id: UUID, acl_principals: Iterable[str]) -> bool:
        """Whether a resource of ``tenant_id`` granted to ``acl_principals`` is visible."""
        if tenant_id != self.tenant_id:
            return False
        if self.is_tenant_admin:
            return True
        return not set(self.acl_principals()).isdisjoint(acl_principals)

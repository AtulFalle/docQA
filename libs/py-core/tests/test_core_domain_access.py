"""Principal and principal set (ADR 0006, section 5)."""

from uuid import uuid4

import pytest

from docqa_core.domain import TENANT_PRINCIPAL, Principal, group_principal, user_principal
from docqa_core.value_sets import UserRole

TENANT = uuid4()
OTHER_TENANT = uuid4()
USER = uuid4()
GROUP_A = uuid4()
GROUP_B = uuid4()


def test_principal_set_lists_tenant_user_then_sorted_groups():
    principal = Principal(tenant_id=TENANT, user_id=USER, group_ids=frozenset({GROUP_B, GROUP_A}))

    expected_groups = sorted([group_principal(GROUP_A), group_principal(GROUP_B)])
    assert principal.acl_principals() == (TENANT_PRINCIPAL, f"u:{USER}", *expected_groups)


def test_principal_entries_use_the_adr_0006_prefixes():
    assert TENANT_PRINCIPAL == "t"
    assert user_principal(USER) == f"u:{USER}"
    assert group_principal(GROUP_A) == f"g:{GROUP_A}"


def test_principal_defaults_to_member_without_groups():
    principal = Principal(tenant_id=TENANT, user_id=USER)

    assert principal.group_ids == frozenset()
    assert principal.role is UserRole.MEMBER
    assert not principal.is_tenant_admin


@pytest.mark.parametrize(
    ("granted", "visible"),
    [
        ([TENANT_PRINCIPAL], True),
        ([f"u:{USER}"], True),
        ([f"g:{GROUP_A}"], True),
        ([f"u:{uuid4()}", f"g:{uuid4()}"], False),
        ([], False),
    ],
)
def test_principal_can_access_when_any_entry_matches(granted, visible):
    principal = Principal(tenant_id=TENANT, user_id=USER, group_ids=frozenset({GROUP_A}))

    assert principal.can_access(tenant_id=TENANT, acl_principals=granted) is visible


def test_principal_never_sees_another_tenant_even_with_a_matching_grant():
    principal = Principal(tenant_id=TENANT, user_id=USER, role=UserRole.ADMIN)

    assert not principal.can_access(tenant_id=OTHER_TENANT, acl_principals=[TENANT_PRINCIPAL])


def test_tenant_admin_sees_every_document_in_the_tenant():
    admin = Principal(tenant_id=TENANT, user_id=USER, role=UserRole.ADMIN)

    assert admin.is_tenant_admin
    assert admin.can_access(tenant_id=TENANT, acl_principals=[])


def test_principal_is_immutable_and_hashable():
    principal = Principal(tenant_id=TENANT, user_id=USER)

    with pytest.raises(AttributeError):
        principal.user_id = uuid4()  # type: ignore[misc]
    assert principal == Principal(tenant_id=TENANT, user_id=USER)
    assert len({principal, Principal(tenant_id=TENANT, user_id=USER)}) == 1

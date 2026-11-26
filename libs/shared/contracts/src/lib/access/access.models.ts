/** Who an ACL entry grants access to. Mirrors PrincipalType in docqa_core and the CHECK. */
export const PRINCIPAL_TYPES = ['user', 'group', 'tenant'] as const;
export type PrincipalType = (typeof PRINCIPAL_TYPES)[number];

/** What an ACL entry grants. Each level includes the ones before it (read < write < admin). */
export const PERMISSIONS = ['read', 'write', 'admin'] as const;
export type Permission = (typeof PERMISSIONS)[number];

/** A user's role in their tenant. Tenant admins see every document. Mirrors UserRole. */
export const USER_ROLES = ['member', 'admin'] as const;
export type UserRole = (typeof USER_ROLES)[number];

/** Where a group or membership comes from: created in docQA, or synced from Keycloak. */
export const MEMBERSHIP_SOURCES = ['local', 'idp'] as const;
export type MembershipSource = (typeof MEMBERSHIP_SOURCES)[number];

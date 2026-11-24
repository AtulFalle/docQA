/** Who an ACL entry grants access to. Mirrors docqa_core and the DB column values. */
export const PRINCIPAL_TYPES = ['user', 'group', 'tenant'] as const;
export type PrincipalType = (typeof PRINCIPAL_TYPES)[number];

/** What an ACL entry grants. */
export const PERMISSIONS = ['read', 'write', 'admin'] as const;
export type Permission = (typeof PERMISSIONS)[number];

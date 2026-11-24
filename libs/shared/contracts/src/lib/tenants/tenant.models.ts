/** Allowed tenant states. Mirrors the Python StrEnum in docqa_core and the DB column values. */
export const TENANT_STATUSES = ['active', 'suspended'] as const;
export type TenantStatus = (typeof TENANT_STATUSES)[number];

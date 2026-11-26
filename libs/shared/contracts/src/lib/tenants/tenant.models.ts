/** Tenant lifecycle. Mirrors TenantStatus in docqa_core and the tenants.status CHECK. */
export const TENANT_STATUSES = ['active', 'suspended', 'deleting'] as const;
export type TenantStatus = (typeof TENANT_STATUSES)[number];

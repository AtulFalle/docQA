/** Allowed values for enum-like VarChar(32) columns; mirrors the Python StrEnums in docqa_core. */

export const TENANT_STATUSES = ['active', 'suspended'] as const;
export type TenantStatus = (typeof TENANT_STATUSES)[number];

export const DOCUMENT_STATUSES = ['pending', 'processing', 'ready', 'failed', 'deleted'] as const;
export type DocumentStatus = (typeof DOCUMENT_STATUSES)[number];

export const PRINCIPAL_TYPES = ['user', 'group', 'tenant'] as const;
export type PrincipalType = (typeof PRINCIPAL_TYPES)[number];

export const PERMISSIONS = ['read', 'write', 'admin'] as const;
export type Permission = (typeof PERMISSIONS)[number];

export const JOB_KINDS = ['ingest', 'reindex', 'delete', 'permission_sync'] as const;
export type JobKind = (typeof JOB_KINDS)[number];

export const JOB_STATUSES = ['queued', 'running', 'succeeded', 'failed', 'cancelled'] as const;
export type JobStatus = (typeof JOB_STATUSES)[number];

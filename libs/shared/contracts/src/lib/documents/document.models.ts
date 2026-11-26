/**
 * Document lifecycle (documents.status). Ingestion state lives on the versions; the status
 * shown to users is derived from the current or newest version. Mirrors DocumentStatus in
 * docqa_core and the CHECK constraint.
 */
export const DOCUMENT_STATUSES = ['active', 'deleting'] as const;
export type DocumentStatus = (typeof DOCUMENT_STATUSES)[number];

/** Ingestion state of one document version. Mirrors VersionStatus in docqa_core. */
export const VERSION_STATUSES = [
    'pending',
    'scanning',
    'processing',
    'ready',
    'failed',
    'rejected',
] as const;
export type VersionStatus = (typeof VERSION_STATUSES)[number];

/** Why a version was rejected. Rejections are never retried. Mirrors RejectionReason. */
export const REJECTION_REASONS = [
    'too_large',
    'too_many_pages',
    'too_many_chunks',
    'unsupported_type',
    'encrypted',
    'infected',
    'duplicate',
    'hash_mismatch',
    'quota_exceeded',
] as const;
export type RejectionReason = (typeof REJECTION_REASONS)[number];

/** State of a presigned multipart upload. Mirrors UploadStatus in docqa_core. */
export const UPLOAD_STATUSES = ['initiated', 'completed', 'aborted', 'expired'] as const;
export type UploadStatus = (typeof UPLOAD_STATUSES)[number];

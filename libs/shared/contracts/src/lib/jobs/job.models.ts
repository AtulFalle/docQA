/** Background job kinds and states. Mirrors JobKind and JobStatus in docqa_core and the CHECKs. */
export const JOB_KINDS = ['ingest', 'reindex', 'delete', 'purge', 'permission_sync'] as const;
export type JobKind = (typeof JOB_KINDS)[number];

export const JOB_STATUSES = ['queued', 'running', 'succeeded', 'failed', 'cancelled'] as const;
export type JobStatus = (typeof JOB_STATUSES)[number];

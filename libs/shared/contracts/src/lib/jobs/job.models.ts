/** Background job kinds and states. Mirrors docqa_core and the DB column values. */
export const JOB_KINDS = ['ingest', 'reindex', 'delete', 'permission_sync'] as const;
export type JobKind = (typeof JOB_KINDS)[number];

export const JOB_STATUSES = ['queued', 'running', 'succeeded', 'failed', 'cancelled'] as const;
export type JobStatus = (typeof JOB_STATUSES)[number];

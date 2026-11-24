/** Document lifecycle states. Mirrors the Python StrEnum in docqa_core and the DB column values. */
export const DOCUMENT_STATUSES = ['pending', 'processing', 'ready', 'failed', 'deleted'] as const;
export type DocumentStatus = (typeof DOCUMENT_STATUSES)[number];

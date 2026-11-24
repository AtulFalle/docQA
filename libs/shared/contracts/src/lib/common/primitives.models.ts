/** Shared scalar aliases. They document intent at the boundary; values are plain strings on the wire. */

/** UUID primary key, as serialised by the backend (e.g. `"0b6f…"`). */
export type Id = string;

/** ISO-8601 timestamp with timezone, e.g. `"2026-11-24T17:08:21.187Z"`. Parse with `new Date()`. */
export type IsoDateTime = string;

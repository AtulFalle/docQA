/** Query parameters for list endpoints (cursor-based). */
export interface PageQuery {
    /** Max items to return; the backend caps it. */
    limit?: number;
    /** Opaque cursor from a previous page's `nextCursor`. */
    cursor?: string;
}

/** One page of a list endpoint response. */
export interface Page<T> {
    items: T[];
    /** Absent on the last page. */
    nextCursor?: string;
}

/** Error envelope returned by every backend endpoint on failure. */
export interface ApiErrorResponse {
    statusCode: number;
    error: string;
    message: string;
    requestId?: string;
}

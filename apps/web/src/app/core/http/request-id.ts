import { HttpErrorResponse } from '@angular/common/http';

/**
 * The request id of a failed backend call, for showing to the user as a support reference.
 * Read from the response header, or from the error body (`ApiErrorResponse.requestId`).
 * Undefined when the request never reached the backend, since then there is nothing to trace.
 */
export function requestIdOf(err: unknown): string | undefined {
    if (!(err instanceof HttpErrorResponse)) return undefined;
    const fromHeader = err.headers.get('X-Request-ID');
    if (fromHeader) return fromHeader;
    const body: unknown = err.error;
    if (typeof body === 'object' && body !== null && 'requestId' in body) {
        const id = (body as { requestId: unknown }).requestId;
        return typeof id === 'string' ? id : undefined;
    }
    return undefined;
}

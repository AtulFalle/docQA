import { AsyncLocalStorage } from 'node:async_hooks';
import { randomUUID } from 'node:crypto';
import { type IncomingMessage, type ServerResponse } from 'node:http';

export const REQUEST_ID_HEADER = 'X-Request-ID';

/** Per-request values added to every log line and forwarded to downstream services. */
export interface RequestContext {
    readonly requestId: string;
    tenantId?: string;
    userId?: string;
}

const storage = new AsyncLocalStorage<RequestContext>();

/** The context of the request being handled, or undefined outside a request. */
export function currentRequestContext(): RequestContext | undefined {
    return storage.getStore();
}

/** Records who made the request (set by auth in M1c) so logs carry tenant and user. */
export function setRequestUser(tenantId: string, userId: string): void {
    const ctx = storage.getStore();
    if (ctx) {
        ctx.tenantId = tenantId;
        ctx.userId = userId;
    }
}

function incomingRequestId(req: IncomingMessage): string | undefined {
    const raw = req.headers['x-request-id'];
    const value = Array.isArray(raw) ? raw[0] : raw;
    return value ? value : undefined;
}

/**
 * Express middleware, registered first in main.ts: accepts or creates the request id, echoes it
 * in the response, and runs the rest of the request inside its context.
 */
export function requestContextMiddleware(
    req: IncomingMessage,
    res: ServerResponse,
    next: () => void,
): void {
    const requestId = incomingRequestId(req) ?? randomUUID();
    req.headers['x-request-id'] = requestId;
    res.setHeader(REQUEST_ID_HEADER, requestId);
    storage.run({ requestId }, next);
}

/** Request id for pino-http: the one set by the middleware, or a new one when it did not run. */
export function requestIdFor(req: IncomingMessage, res: ServerResponse): string {
    const id = incomingRequestId(req) ?? randomUUID();
    if (!res.headersSent) {
        res.setHeader(REQUEST_ID_HEADER, id);
    }
    return id;
}

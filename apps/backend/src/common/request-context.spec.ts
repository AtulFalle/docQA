import { type IncomingMessage, type ServerResponse } from 'node:http';
import {
    currentRequestContext,
    requestContextMiddleware,
    requestIdFor,
    setRequestUser,
} from './request-context';
import { correlationFields } from './logger.config';

function fakeReq(headers: Record<string, string> = {}): IncomingMessage {
    return { headers: { ...headers } } as unknown as IncomingMessage;
}

function fakeRes(): ServerResponse & { headers: Record<string, string> } {
    const headers: Record<string, string> = {};
    return {
        headers,
        headersSent: false,
        setHeader: (name: string, value: string) => {
            headers[name] = value;
        },
    } as unknown as ServerResponse & { headers: Record<string, string> };
}

describe('requestContextMiddleware', () => {
    it('keeps an incoming request id and exposes it to the handler', () => {
        const req = fakeReq({ 'x-request-id': 'abc' });
        const res = fakeRes();
        let seen: string | undefined;
        requestContextMiddleware(req, res, () => {
            seen = currentRequestContext()?.requestId;
        });
        expect(seen).toBe('abc');
        expect(res.headers['X-Request-ID']).toBe('abc');
    });

    it('creates a request id and writes it back to the request headers', () => {
        const req = fakeReq();
        const res = fakeRes();
        requestContextMiddleware(req, res, () => undefined);
        expect(req.headers['x-request-id']).toMatch(/^[0-9a-f-]{36}$/);
        expect(requestIdFor(req, fakeRes())).toBe(req.headers['x-request-id']);
    });

    it('adds tenant and user to log fields once set', () => {
        let fields: Record<string, string> = {};
        requestContextMiddleware(fakeReq(), fakeRes(), () => {
            setRequestUser('t1', 'u1');
            fields = correlationFields();
        });
        expect(fields).toMatchObject({ tenant_id: 't1', user_id: 'u1' });
    });

    it('has no context outside a request', () => {
        expect(currentRequestContext()).toBeUndefined();
        expect(correlationFields()).toEqual({});
    });
});

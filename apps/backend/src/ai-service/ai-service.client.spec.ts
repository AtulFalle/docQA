import { type IncomingMessage, type ServerResponse } from 'node:http';
import { type MiddlewareCallbackParams } from 'openapi-fetch';
import { requestContextMiddleware } from '../common/request-context';
import { forwardRequestId } from './ai-service.client';

async function outgoing(): Promise<Request> {
    const request = new Request('http://ai-api/healthz');
    const params = { request } as unknown as MiddlewareCallbackParams & { request: Request };
    const result = await forwardRequestId.onRequest?.(params);
    return result instanceof Request ? result : request;
}

describe('forwardRequestId', () => {
    it('sends the current request id to ai-api', async () => {
        const req = { headers: { 'x-request-id': 'req-42' } } as unknown as IncomingMessage;
        const res = { setHeader: () => undefined } as unknown as ServerResponse;
        let sent: string | null = null;
        await new Promise<void>((done) => {
            requestContextMiddleware(req, res, () => {
                void outgoing().then((r) => {
                    sent = r.headers.get('X-Request-ID');
                    done();
                });
            });
        });
        expect(sent).toBe('req-42');
    });

    it('sends nothing outside a request', async () => {
        expect((await outgoing()).headers.has('X-Request-ID')).toBe(false);
    });
});

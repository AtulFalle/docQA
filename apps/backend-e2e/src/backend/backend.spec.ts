import { type ApiErrorResponse, type InfoResponse, type LivenessResponse } from '@docqa/contracts';

const baseUrl = `http://${process.env.HOST ?? 'localhost'}:${process.env.PORT ?? 3000}`;

describe('backend API', () => {
    it('GET /api/v1/health returns ok', async () => {
        const res = await fetch(`${baseUrl}/api/v1/health`);
        expect(res.status).toBe(200);
        expect((await res.json()) as LivenessResponse).toEqual({ status: 'ok' });
    });

    it('echoes a provided X-Request-ID', async () => {
        const res = await fetch(`${baseUrl}/api/v1/health`, {
            headers: { 'x-request-id': 'e2e-123' },
        });
        expect(res.headers.get('x-request-id')).toBe('e2e-123');
    });

    it('generates X-Request-ID when absent', async () => {
        const res = await fetch(`${baseUrl}/api/v1/health`);
        expect(res.headers.get('x-request-id')).toMatch(/^[0-9a-f-]{36}$/);
    });

    it('GET /api/v1/info returns service metadata', async () => {
        const res = await fetch(`${baseUrl}/api/v1/info`);
        expect(res.status).toBe(200);
        const body = (await res.json()) as InfoResponse;
        expect(body).toEqual({
            service: expect.any(String),
            version: expect.any(String),
            environment: expect.any(String),
        });
    });

    it('unknown route returns the 404 error envelope', async () => {
        const res = await fetch(`${baseUrl}/api/v1/does-not-exist`, {
            headers: { 'x-request-id': 'e2e-404' },
        });
        expect(res.status).toBe(404);
        const body = (await res.json()) as ApiErrorResponse;
        expect(body).toMatchObject({ statusCode: 404, error: 'Not Found', requestId: 'e2e-404' });
        expect(typeof body.message).toBe('string');
    });
});

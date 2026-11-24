import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { type ReadinessResponse } from '@docqa/contracts';
import { ApiClient } from './api-client';

describe('ApiClient', () => {
    let api: ApiClient;
    let http: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [provideHttpClient(), provideHttpClientTesting()],
        });
        api = TestBed.inject(ApiClient);
        http = TestBed.inject(HttpTestingController);
    });

    afterEach(() => http.verify());

    it('calls the versioned endpoints', () => {
        api.liveness().subscribe();
        api.info().subscribe();
        api.readiness().subscribe();
        http.expectOne('/api/v1/health').flush({ status: 'ok' });
        http.expectOne('/api/v1/info').flush({ service: 's', version: '1', environment: 'e' });
        http.expectOne('/api/v1/health/ready').flush({ status: 'ok', info: {}, error: {} });
    });

    it('maps a 503 readiness body to a value', () => {
        const body: ReadinessResponse = {
            status: 'error',
            info: { database: { status: 'up' } },
            error: { aiService: { status: 'down' } },
        };
        let result: ReadinessResponse | undefined;
        api.readiness().subscribe((r) => (result = r));
        http.expectOne('/api/v1/health/ready').flush(body, {
            status: 503,
            statusText: 'Service Unavailable',
        });
        expect(result).toEqual(body);
    });

    it('propagates other errors', () => {
        let failed = false;
        api.readiness().subscribe({ error: () => (failed = true) });
        http.expectOne('/api/v1/health/ready').flush('boom', {
            status: 500,
            statusText: 'Server Error',
        });
        expect(failed).toBe(true);
    });

    it('propagates a 503 without a readiness body', () => {
        let failed = false;
        api.readiness().subscribe({ error: () => (failed = true) });
        http.expectOne('/api/v1/health/ready').flush('down', {
            status: 503,
            statusText: 'Service Unavailable',
        });
        expect(failed).toBe(true);
    });
});

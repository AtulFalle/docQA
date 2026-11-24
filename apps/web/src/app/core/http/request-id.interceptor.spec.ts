import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { requestIdInterceptor } from './request-id.interceptor';

describe('requestIdInterceptor', () => {
    let client: HttpClient;
    let http: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(withInterceptors([requestIdInterceptor])),
                provideHttpClientTesting(),
            ],
        });
        client = TestBed.inject(HttpClient);
        http = TestBed.inject(HttpTestingController);
    });

    afterEach(() => http.verify());

    it('adds X-Request-ID to api requests', () => {
        client.get('/api/v1/info').subscribe();
        const req = http.expectOne('/api/v1/info');
        expect(req.request.headers.get('X-Request-ID')).toMatch(/^[0-9a-f-]{36}$/);
        req.flush({});
    });

    it('preserves an existing X-Request-ID', () => {
        client.get('/api/v1/info', { headers: { 'X-Request-ID': 'abc' } }).subscribe();
        const req = http.expectOne('/api/v1/info');
        expect(req.request.headers.get('X-Request-ID')).toBe('abc');
        req.flush({});
    });

    it('ignores non-api requests', () => {
        client.get('/assets/x.json').subscribe();
        const req = http.expectOne('/assets/x.json');
        expect(req.request.headers.has('X-Request-ID')).toBe(false);
        req.flush({});
    });
});

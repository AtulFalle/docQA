import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { StatusPage } from './status-page';

const URL = '/api/v1/health/ready';

describe('StatusPage', () => {
    function setup() {
        TestBed.configureTestingModule({
            imports: [StatusPage],
            providers: [provideHttpClient(), provideHttpClientTesting()],
        });
        const fixture = TestBed.createComponent(StatusPage);
        const http = TestBed.inject(HttpTestingController);
        return { fixture, http, el: fixture.nativeElement as HTMLElement };
    }

    it('shows loading first', async () => {
        const { fixture, el, http } = setup();
        await fixture.whenStable();
        expect(el.textContent).toContain('Checking');
        http.expectOne(URL);
    });

    it('renders the ok state', async () => {
        const { fixture, el, http } = setup();
        http.expectOne(URL).flush({
            status: 'ok',
            info: { database: { status: 'up' }, aiService: { status: 'up' } },
            error: {},
        });
        await fixture.whenStable();
        expect(el.textContent).toContain('All systems operational');
        expect(el.querySelectorAll('el-list-item').length).toBe(2);
        expect(el.querySelectorAll('.status__state.status__state--up').length).toBe(2);
    });

    it('renders the degraded state', async () => {
        const { fixture, el, http } = setup();
        http.expectOne(URL).flush(
            {
                status: 'error',
                info: { database: { status: 'up' } },
                error: { aiService: { status: 'down', message: 'timeout' } },
            },
            { status: 503, statusText: 'Service Unavailable' },
        );
        await fixture.whenStable();
        expect(el.textContent).toContain('Degraded');
        expect(el.textContent).toContain('aiService');
        expect(el.textContent).toContain('timeout');
        expect(el.querySelectorAll('.status__state.status__state--down').length).toBe(1);
    });

    it('shows the request id as a support reference on error', async () => {
        const { fixture, el, http } = setup();
        http.expectOne(URL).flush(
            { statusCode: 500, error: 'Internal Server Error', message: 'x', requestId: 'req-9' },
            { status: 500, statusText: 'Server Error' },
        );
        await fixture.whenStable();
        expect(el.querySelector('[role="alert"]')?.textContent).toContain('Reference: req-9');
    });

    it('renders the error state and can refresh', async () => {
        const { fixture, el, http } = setup();
        http.expectOne(URL).flush('x', { status: 500, statusText: 'Server Error' });
        await fixture.whenStable();
        expect(el.querySelector('[role="alert"]')).not.toBeNull();
        (el.querySelector('button') as HTMLButtonElement).click();
        http.expectOne(URL).flush({ status: 'ok', info: {}, error: {} });
        await fixture.whenStable();
        expect(el.querySelector('[role="alert"]')).toBeNull();
        expect(el.textContent).toContain('All systems operational');
    });
});

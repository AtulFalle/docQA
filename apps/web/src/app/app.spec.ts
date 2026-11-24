import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App', () => {
    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [App],
            providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
        });
    });

    it('renders brand and nav links', async () => {
        const fixture = TestBed.createComponent(App);
        TestBed.inject(HttpTestingController).expectOne('/api/v1/info').flush({
            service: 'docqa-backend',
            version: '1.2.3',
            environment: 'test',
        });
        await fixture.whenStable();
        const el = fixture.nativeElement as HTMLElement;
        expect(el.querySelector('.brand')?.textContent).toContain('docQA');
        const links = Array.from(el.querySelectorAll('nav a')).map((a) => a.textContent?.trim());
        expect(links).toEqual(['Status', 'Ask']);
        expect(el.querySelector('footer')?.textContent).toContain('v1.2.3');
    });

    it('degrades gracefully when info fails', async () => {
        const fixture = TestBed.createComponent(App);
        TestBed.inject(HttpTestingController)
            .expectOne('/api/v1/info')
            .flush('x', { status: 500, statusText: 'Server Error' });
        await fixture.whenStable();
        expect(
            (fixture.nativeElement as HTMLElement).querySelector('footer')?.textContent,
        ).toContain('unavailable');
    });
});

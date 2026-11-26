import { HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { requestIdOf } from './request-id';

describe('requestIdOf', () => {
    it('reads the response header first', () => {
        const err = new HttpErrorResponse({
            status: 500,
            headers: new HttpHeaders({ 'X-Request-ID': 'from-header' }),
            error: { requestId: 'from-body' },
        });
        expect(requestIdOf(err)).toBe('from-header');
    });

    it('falls back to the error body', () => {
        const err = new HttpErrorResponse({ status: 404, error: { requestId: 'from-body' } });
        expect(requestIdOf(err)).toBe('from-body');
    });

    it('is undefined when the backend was not reached', () => {
        expect(requestIdOf(new HttpErrorResponse({ status: 0 }))).toBeUndefined();
        expect(requestIdOf(new Error('x'))).toBeUndefined();
    });
});

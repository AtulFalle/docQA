import { type HttpInterceptorFn } from '@angular/common/http';

/** Adds a correlation id to every backend request unless the caller already set one. */
export const requestIdInterceptor: HttpInterceptorFn = (req, next) => {
    if (!req.url.startsWith('/api/') || req.headers.has('X-Request-ID')) {
        return next(req);
    }
    return next(req.clone({ setHeaders: { 'X-Request-ID': crypto.randomUUID() } }));
};

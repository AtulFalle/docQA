import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { type InfoResponse, type LivenessResponse, type ReadinessResponse } from '@docqa/contracts';
import { type Observable, catchError, of, throwError } from 'rxjs';

const BASE = '/api/v1';

function isReadinessBody(body: unknown): body is ReadinessResponse {
    return typeof body === 'object' && body !== null && 'status' in body;
}

@Injectable({ providedIn: 'root' })
export class ApiClient {
    private readonly http = inject(HttpClient);

    liveness(): Observable<LivenessResponse> {
        return this.http.get<LivenessResponse>(`${BASE}/health`);
    }

    /** The backend answers 503 with a ReadinessResponse body when a dependency is down; that is data, not an error. */
    readiness(): Observable<ReadinessResponse> {
        return this.http
            .get<ReadinessResponse>(`${BASE}/health/ready`)
            .pipe(
                catchError((err: unknown) =>
                    err instanceof HttpErrorResponse &&
                    err.status === 503 &&
                    isReadinessBody(err.error)
                        ? of(err.error)
                        : throwError(() => err),
                ),
            );
    }

    info(): Observable<InfoResponse> {
        return this.http.get<InfoResponse>(`${BASE}/info`);
    }
}

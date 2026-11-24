/**
 * Public HTTP contracts shared by the Angular app (apps/web) and the NestJS backend (apps/backend).
 * Types only — no runtime code — so both sides can import them without bundling server code.
 */

export type HealthStatus = 'ok' | 'error' | 'degraded' | 'shutting_down';

/** GET /api/v1/health — liveness. */
export interface LivenessResponse {
    status: HealthStatus;
}

/** Per-dependency readiness, e.g. { database: { status: 'up' }, aiService: { status: 'down' } }. */
export type DependencyChecks = Record<
    string,
    { status: 'up' | 'degraded' | 'down'; message?: string }
>;

/** GET /api/v1/health/ready — readiness of the backend and its dependencies. */
export interface ReadinessResponse {
    status: HealthStatus;
    info: DependencyChecks;
    error: DependencyChecks;
}

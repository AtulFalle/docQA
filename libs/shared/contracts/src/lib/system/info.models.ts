/** GET /api/v1/info — build/runtime metadata. */
export interface InfoResponse {
    service: string;
    version: string;
    environment: string;
}

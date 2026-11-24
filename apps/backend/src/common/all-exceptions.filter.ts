import { STATUS_CODES } from 'node:http';
import {
    type ArgumentsHost,
    Catch,
    type ExceptionFilter,
    HttpException,
    HttpStatus,
} from '@nestjs/common';
import { PinoLogger } from 'nestjs-pino';
import { type ApiErrorResponse } from '@docqa/contracts';

interface RequestLike {
    id?: unknown;
}

interface ResponseLike {
    status(code: number): ResponseLike;
    json(body: unknown): unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function toRequestId(id: unknown): string | undefined {
    return id === undefined || id === null ? undefined : String(id);
}

function isHealthCheckBody(body: unknown): boolean {
    return isRecord(body) && ('info' in body || 'details' in body);
}

function messageFrom(raw: unknown, fallback: string): string {
    if (Array.isArray(raw)) {
        return raw.map(String).join('; ');
    }
    return typeof raw === 'string' ? raw : fallback;
}

function describeHttpException(
    exception: HttpException,
    body: unknown,
): { message: string; error: string | undefined } {
    if (typeof body === 'string') {
        return { message: body, error: undefined };
    }
    if (!isRecord(body)) {
        return { message: exception.message, error: undefined };
    }
    const error = typeof body['error'] === 'string' ? body['error'] : undefined;
    return { message: messageFrom(body['message'], exception.message), error };
}

/** Maps every thrown error to the shared ApiErrorResponse envelope; never leaks stack traces. */
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
    constructor(private readonly logger: PinoLogger) {
        this.logger.setContext(AllExceptionsFilter.name);
    }

    catch(exception: unknown, host: ArgumentsHost): void {
        const http = host.switchToHttp();
        const req = http.getRequest<RequestLike>();
        const res = http.getResponse<ResponseLike>();
        const requestId = toRequestId(req.id);

        let statusCode: number = HttpStatus.INTERNAL_SERVER_ERROR;
        let message = 'Internal server error';
        let error: string | undefined;

        if (exception instanceof HttpException) {
            statusCode = exception.getStatus();
            const body = exception.getResponse();
            if (isHealthCheckBody(body)) {
                // Terminus readiness failures: keep the ReadinessResponse body (503).
                res.status(statusCode).json(body);
                return;
            }
            ({ message, error } = describeHttpException(exception, body));
        }

        if (statusCode >= 500) {
            this.logger.error({ err: exception, requestId }, 'Unhandled exception');
            message = statusCode === 500 ? 'Internal server error' : message;
        }

        const payload: ApiErrorResponse = {
            statusCode,
            error: error ?? STATUS_CODES[statusCode] ?? 'Error',
            message,
            ...(requestId !== undefined && { requestId }),
        };
        res.status(statusCode).json(payload);
    }
}

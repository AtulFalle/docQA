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
        const requestId = req.id === undefined || req.id === null ? undefined : String(req.id);

        let statusCode: number = HttpStatus.INTERNAL_SERVER_ERROR;
        let message = 'Internal server error';
        let error: string | undefined;

        if (exception instanceof HttpException) {
            statusCode = exception.getStatus();
            const body = exception.getResponse();
            if (isRecord(body) && ('info' in body || 'details' in body)) {
                // Terminus readiness failures: keep the ReadinessResponse body (503).
                res.status(statusCode).json(body);
                return;
            }
            if (typeof body === 'string') {
                message = body;
            } else if (isRecord(body)) {
                const raw = body['message'];
                if (Array.isArray(raw)) {
                    message = raw.map(String).join('; ');
                } else if (typeof raw === 'string') {
                    message = raw;
                } else {
                    message = exception.message;
                }
                if (typeof body['error'] === 'string') {
                    error = body['error'];
                }
            } else {
                message = exception.message;
            }
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

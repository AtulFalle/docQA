import { type ArgumentsHost, BadRequestException, NotFoundException } from '@nestjs/common';
import { type PinoLogger } from 'nestjs-pino';
import { AllExceptionsFilter } from './all-exceptions.filter';

function setup() {
    const json = jest.fn();
    const status = jest.fn().mockReturnValue({ json });
    const res = { status, json };
    const host = {
        switchToHttp: () => ({ getRequest: () => ({ id: 'req-1' }), getResponse: () => res }),
    } as unknown as ArgumentsHost;
    const logger = { setContext: jest.fn(), error: jest.fn() };
    const filter = new AllExceptionsFilter(logger as unknown as PinoLogger);
    return { filter, host, status, json, logger };
}

describe('AllExceptionsFilter', () => {
    it('wraps HttpException in the envelope with requestId', () => {
        const { filter, host, status, json } = setup();
        filter.catch(new NotFoundException('nope'), host);
        expect(status).toHaveBeenCalledWith(404);
        expect(json).toHaveBeenCalledWith({
            statusCode: 404,
            error: 'Not Found',
            message: 'nope',
            requestId: 'req-1',
        });
    });

    it('joins validation message arrays', () => {
        const { filter, host, json } = setup();
        filter.catch(new BadRequestException(['a bad', 'b bad']), host);
        expect(json).toHaveBeenCalledWith(
            expect.objectContaining({ statusCode: 400, message: 'a bad; b bad' }),
        );
    });

    it('hides internals of unknown errors and logs them', () => {
        const { filter, host, status, json, logger } = setup();
        filter.catch(new Error('db password leaked'), host);
        expect(status).toHaveBeenCalledWith(500);
        expect(json).toHaveBeenCalledWith({
            statusCode: 500,
            error: 'Internal Server Error',
            message: 'Internal server error',
            requestId: 'req-1',
        });
        expect(logger.error).toHaveBeenCalledTimes(1);
    });
});

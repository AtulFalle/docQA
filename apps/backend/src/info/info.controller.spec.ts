import { ConfigService } from '@nestjs/config';
import { Test } from '@nestjs/testing';
import { InfoController } from './info.controller';

describe('InfoController', () => {
    it('returns service metadata from config', async () => {
        const values: Record<string, string> = {
            SERVICE_NAME: 'docqa-backend',
            APP_VERSION: '1.2.3',
            NODE_ENV: 'test',
        };
        const moduleRef = await Test.createTestingModule({
            controllers: [InfoController],
            providers: [{ provide: ConfigService, useValue: { get: (k: string) => values[k] } }],
        }).compile();
        expect(moduleRef.get(InfoController).info()).toEqual({
            service: 'docqa-backend',
            version: '1.2.3',
            environment: 'test',
        });
    });
});

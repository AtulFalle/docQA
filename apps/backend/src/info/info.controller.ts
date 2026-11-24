import { Controller, Get } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { type InfoResponse } from '@docqa/contracts';
import { type Env } from '../config/env';

@Controller({ path: 'info', version: '1' })
export class InfoController {
    constructor(private readonly config: ConfigService<Env, true>) {}

    @Get()
    info(): InfoResponse {
        return {
            service: this.config.get('SERVICE_NAME', { infer: true }),
            version: this.config.get('APP_VERSION', { infer: true }),
            environment: this.config.get('NODE_ENV', { infer: true }),
        };
    }
}

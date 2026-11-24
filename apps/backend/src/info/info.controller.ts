import { Controller, Get } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { type InfoResponse } from '@docqa/contracts';
import { ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import { type Env } from '../config/env';
import { contractRef } from '../openapi/openapi';

@ApiTags('info')
@Controller({ path: 'info', version: '1' })
export class InfoController {
    constructor(private readonly config: ConfigService<Env, true>) {}

    @Get()
    @ApiOperation({ summary: 'Build and runtime metadata' })
    @ApiOkResponse({ schema: contractRef('InfoResponse') })
    info(): InfoResponse {
        return {
            service: this.config.get('SERVICE_NAME', { infer: true }),
            version: this.config.get('APP_VERSION', { infer: true }),
            environment: this.config.get('NODE_ENV', { infer: true }),
        };
    }
}

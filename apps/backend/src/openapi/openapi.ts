import { writeFileSync } from 'node:fs';
import { type INestApplication } from '@nestjs/common';
import { DocumentBuilder, type OpenAPIObject, SwaggerModule } from '@nestjs/swagger';

/** Name of a model exported by @docqa/contracts. */
export type ContractName = 'InfoResponse' | 'LivenessResponse' | 'ReadinessResponse';

/**
 * Points a response at a model in @docqa/contracts. `make contracts` fills in
 * `components.schemas` from the TypeScript models, so they stay the single source of truth.
 */
export function contractRef(name: ContractName): { $ref: string } {
    return { $ref: `#/components/schemas/${name}` };
}

/** Builds the public API's OpenAPI document from the controllers' decorators. */
export function buildOpenApiDocument(app: INestApplication): OpenAPIObject {
    const config = new DocumentBuilder()
        .setTitle('docQA API')
        .setDescription('Public API of the docQA backend.')
        .setVersion('1')
        .build();
    return SwaggerModule.createDocument(app, config);
}

/** Writes the document as indented JSON so the committed copy diffs cleanly. */
export function writeOpenApiDocument(app: INestApplication, path: string): void {
    writeFileSync(path, `${JSON.stringify(buildOpenApiDocument(app), null, 2)}\n`, 'utf8');
}

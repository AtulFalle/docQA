/**
 * OpenTelemetry bootstrap. Must be the first import of main.ts so auto-instrumentation can patch
 * modules before they load. This is the only file that reads process.env directly, because the
 * config module is not booted yet.
 */
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

if (process.env['OTEL_ENABLED'] === 'true') {
    const sdk = new NodeSDK({
        serviceName: process.env['SERVICE_NAME'] ?? 'docqa-backend',
        traceExporter: new OTLPTraceExporter({ url: process.env['OTEL_EXPORTER_OTLP_ENDPOINT'] }),
        instrumentations: [
            getNodeAutoInstrumentations({
                '@opentelemetry/instrumentation-fs': { enabled: false },
            }),
        ],
    });
    sdk.start();

    process.once('SIGTERM', () => {
        sdk.shutdown().catch(() => undefined);
    });
}

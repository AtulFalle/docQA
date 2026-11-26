/**
 * OpenTelemetry bootstrap. Must be the first import of main.ts so auto-instrumentation can patch
 * modules before they load. This is the only file that reads process.env directly, because the
 * config module is not booted yet.
 *
 * Exports traces, logs and metrics over OTLP/gRPC. Logs come from pino through the pino
 * instrumentation, so the same JSON line written to stdout is also searchable in Loki.
 */
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-grpc';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-grpc';
import { BatchLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { defaultResource, resourceFromAttributes } from '@opentelemetry/resources';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

if (process.env['OTEL_ENABLED'] === 'true') {
    const url = process.env['OTEL_EXPORTER_OTLP_ENDPOINT'];
    const sdk = new NodeSDK({
        resource: defaultResource().merge(
            resourceFromAttributes({
                'service.name': process.env['SERVICE_NAME'] ?? 'docqa-backend',
                'service.version': process.env['APP_VERSION'] ?? '0.1.0',
                'deployment.environment': process.env['APP_ENV'] ?? 'local',
            }),
        ),
        traceExporter: new OTLPTraceExporter({ url }),
        logRecordProcessors: [
            new BatchLogRecordProcessor({ exporter: new OTLPLogExporter({ url }) }),
        ],
        metricReaders: [
            new PeriodicExportingMetricReader({ exporter: new OTLPMetricExporter({ url }) }),
        ],
        instrumentations: [
            getNodeAutoInstrumentations({
                '@opentelemetry/instrumentation-fs': { enabled: false },
                // trace_id/span_id are already added by the logger mixin (common/logger.config.ts).
                '@opentelemetry/instrumentation-pino': { disableLogCorrelation: true },
            }),
        ],
    });
    sdk.start();

    process.once('SIGTERM', () => {
        sdk.shutdown().catch(() => undefined);
    });
}

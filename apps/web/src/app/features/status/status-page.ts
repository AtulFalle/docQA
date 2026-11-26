import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { type HealthStatus, type ReadinessResponse } from '@docqa/contracts';
import { Subject, catchError, map, of, startWith, switchMap } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { requestIdOf } from '../../core/http/request-id';

type State =
    | { kind: 'loading' }
    | { kind: 'error'; requestId?: string }
    | { kind: 'loaded'; data: ReadinessResponse };

interface Row {
    name: string;
    up: boolean;
    message?: string;
}

const OVERALL: Record<HealthStatus, string> = {
    ok: 'All systems operational',
    error: 'Degraded: a dependency is down',
    degraded: 'Degraded: a dependency is impaired',
    shutting_down: 'Shutting down',
};

@Component({
    selector: 'dq-status-page',
    templateUrl: './status-page.html',
    styleUrl: './status-page.scss',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatusPage {
    private readonly api = inject(ApiClient);
    private readonly reload$ = new Subject<void>();

    protected readonly state = toSignal(
        this.reload$.pipe(
            startWith(undefined),
            switchMap(() =>
                this.api.readiness().pipe(
                    map((data): State => ({ kind: 'loaded', data })),
                    catchError((err: unknown) =>
                        of<State>({ kind: 'error', requestId: requestIdOf(err) }),
                    ),
                    startWith<State>({ kind: 'loading' }),
                ),
            ),
        ),
        { initialValue: { kind: 'loading' } as State },
    );

    protected readonly overall = computed(() => {
        const s = this.state();
        return s.kind === 'loaded'
            ? { ok: s.data.status === 'ok', label: OVERALL[s.data.status] }
            : null;
    });

    protected readonly rows = computed<Row[]>(() => {
        const s = this.state();
        if (s.kind !== 'loaded') return [];
        const toRows = (checks: ReadinessResponse['info']): Row[] =>
            Object.entries(checks).map(([name, c]) => ({
                name,
                up: c.status === 'up',
                message: c.message,
            }));
        return [...toRows(s.data.info), ...toRows(s.data.error)].sort((a, b) =>
            a.name.localeCompare(b.name),
        );
    });

    /** Support reference shown with the error, so the failure can be found in the logs. */
    protected readonly errorReference = computed(() => {
        const s = this.state();
        return s.kind === 'error' ? s.requestId : undefined;
    });

    protected refresh(): void {
        this.reload$.next();
    }
}

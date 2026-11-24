import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { catchError, of } from 'rxjs';
import { ApiClient } from './core/api/api-client';

@Component({
    imports: [RouterOutlet, RouterLink, RouterLinkActive],
    selector: 'dq-root',
    templateUrl: './app.html',
    styleUrl: './app.scss',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
    protected readonly info = toSignal(
        inject(ApiClient)
            .info()
            .pipe(catchError(() => of(null))),
        {
            initialValue: null,
        },
    );
}

import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
    selector: 'dq-not-found-page',
    imports: [RouterLink],
    template: `
        <h1>Page not found</h1>
        <p>The page you are looking for does not exist.</p>
        <a routerLink="/">Back to status</a>
    `,
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundPage {}

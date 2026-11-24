import { type Route } from '@angular/router';

export const appRoutes: Route[] = [
    {
        path: '',
        pathMatch: 'full',
        title: 'System status',
        loadComponent: () => import('./features/status/status-page').then((m) => m.StatusPage),
    },
    {
        path: 'ask',
        title: 'Ask',
        loadComponent: () => import('./features/ask/ask-page').then((m) => m.AskPage),
    },
    {
        path: '**',
        title: 'Page not found',
        loadComponent: () =>
            import('./features/not-found/not-found-page').then((m) => m.NotFoundPage),
    },
];

import {
    type ApplicationConfig,
    inject,
    provideAppInitializer,
    provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { ElThemeService, provideElTheme } from '@docqa/ui/theme/theme';
import { appRoutes } from './app.routes';
import { requestIdInterceptor } from './core/http/request-id.interceptor';

export const appConfig: ApplicationConfig = {
    providers: [
        provideBrowserGlobalErrorListeners(),
        provideRouter(appRoutes, withComponentInputBinding()),
        provideHttpClient(withFetch(), withInterceptors([requestIdInterceptor])),
        provideElTheme({ mode: 'light' }),
        // Create the theme service at startup so it sets data-el-theme on <html>.
        provideAppInitializer(() => void inject(ElThemeService)),
    ],
};

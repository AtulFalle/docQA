import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

// eslint-disable-next-line no-console -- last-resort report when bootstrap fails
bootstrapApplication(App, appConfig).catch((err) => console.error(err));

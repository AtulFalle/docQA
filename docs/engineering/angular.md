# Angular standards

Applies to `apps/web` (Angular 22) and `apps/web-e2e` (Playwright). General TypeScript rules are in [typescript.md](typescript.md); this file adds the Angular layer.

Every rule is tagged:

- **[Enforced: tool/rule]** a tool fails the build, the commit or CI.
- **[Review]** no tool catches it; reviewers check it.

> Enforced in `apps/web/eslint.config.mjs`: OnPush, standalone, signal APIs (`prefer-signals`, `prefer-signal-model`, `prefer-inject`), built-in control flow, self-closing tags, `NgOptimizedImage`, no `$any` in templates, file and function size, and the angular-eslint template accessibility rules. SCSS/BEM is enforced by `stylelint.config.mjs` (`web:lint-styles`). Everything else marked **[Review]** is checked by reviewers.

## Components

- Keep files small: 400 lines max per `.ts`/`.html` file and 50 lines per function. A component that grows past that gets split into child components or moves its logic into a service or pure functions. **[Enforced: `max-lines`, `max-lines-per-function`]**
- Modern APIs only: `input()`, `output()`, `model()`, `viewChild()` and `inject()`, instead of `@Input`/`@Output`/`@ViewChild` and constructor injection. **[Enforced: `prefer-signals`, `prefer-signal-model`, `prefer-inject`]**
- Standalone components only. Do not add NgModules. **[Enforced: @angular-eslint/prefer-standalone]**
- `changeDetection: ChangeDetectionStrategy.OnPush` on every component. **[Enforced: @angular-eslint/prefer-on-push-component-change-detection]**
- The app is zoneless. Do not add `zone.js`, and do not rely on zone-triggered change detection: changes reach the view through signals and explicit markers. **[Review]**
- Selectors use the `dq` prefix: `dq-document-list` (element), `[dqHighlight]` (attribute). **[Enforced: `@angular-eslint/component-selector`, `directive-selector` in `apps/web/eslint.config.mjs`]**

```ts
// bad
@Component({ selector: 'app-docs', template: `...` })
export class DocsComponent {
  @Input() docs: Doc[] = [];
}

// good
@Component({
  selector: 'dq-document-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `...`,
})
export class DocumentListComponent {
  readonly documents = input.required<DocumentSummary[]>();
}
```

## State and signals

- Component state: `signal()`, `computed()`, `linkedSignal()`. Derived values are `computed`, never a method called from the template. **[Review]**
- Inputs and outputs: `input()`, `output()`, `model()`. Do not use `@Input()`/`@Output()` decorators in new code. **[Review]**
- Use `effect()` only for side effects such as DOM or logging. Do not use it to copy state between signals. **[Review]**
- Use `toSignal()` to bring an observable into a template. Keep RxJS for HTTP streams and cancellation. **[Review]**

## Dependency injection

- Use `inject()` in field initialisers, not constructor parameters. **[Review]**
- `providedIn: 'root'` for app-wide services. Feature services are provided by the route or the component that owns them. **[Review]**

```ts
// good
export class DocumentListComponent {
  private readonly documents = inject(DocumentStore);
}
```

## Templates and control flow

- Use the built-in control flow (`@if`, `@for` with `track`, `@switch`, `@defer`). `*ngIf`, `*ngFor` and `ngSwitch` are not used in new code. **[Enforced: `template/prefer-control-flow`]**
- `@for` always has a `track` expression with a stable id. **[Review]**
- No function calls with side effects in templates. No `innerHTML` binding (see Security). **[Review]**

```html
<!-- bad -->
<li *ngFor="let d of docs">{{ d.title }}</li>

<!-- good -->
@for (doc of documents(); track doc.id) {
  <li>{{ doc.title }}</li>
}
```

## Routing

- Feature routes are lazy: `loadComponent` or `loadChildren` for every route except the shell. **[Review]**
- Route guards are functions (`CanMatchFn`, `CanActivateFn`). Guards are a UX convenience; the backend is the authority. **[Review]**
- Route parameters are typed with `input()` through `withComponentInputBinding()`. **[Review]**

## Folder layout

```
apps/web/src/app/
  core/           app-wide singletons: api/ (ApiClient), interceptors/, auth/, layout shell
  shared/         presentational components and pipes with no feature knowledge
  features/
    documents/    one folder per feature: routes.ts, pages/, components/, data/, *.spec.ts
    search/
```

- `features/<name>` never imports another feature's internals. Share through `core/` or `shared/`, or through `@docqa/contracts`. **[Review]**
- `core/` never imports from `features/`. **[Review]**

## HTTP

- All HTTP goes through `core/api/ApiClient`. Components and feature services do not inject `HttpClient` directly. **[Review]**
- Paths are relative to `/api/v1`: `this.api.get<DocumentSummary[]>('documents')`. Never hardcode a host, port or scheme. Dev uses the Angular proxy (`apps/web/proxy.conf.json`, `/api` to the backend); production uses the nginx `/api` location. **[Review]**
- Response and request types come from `@docqa/contracts`. **[Review]**
- Every request carries a request id. The interceptor in `core/interceptors/` sets `X-Request-Id` (a UUID per request) and the backend echoes it into logs. **[Review]**
- Every request has a timeout. The `ApiClient` default is set once; a caller can shorten it, not remove it. **[Review]**
- Map backend errors to the error envelope in one place (`ApiClient`), and show a user message from its `code`. Never show raw server messages or stack traces. **[Review]**

```ts
// bad
this.http.get('http://localhost:3000/api/v1/documents');

// good
this.api.get<DocumentSummary[]>('documents');
```

## Forms

- Typed reactive forms only (`FormGroup<...>`, `FormControl<...>` with `nonNullable`). Template-driven forms are not used. **[Review]**
- Validation rules live in the form, and the server remains the authority. Show server validation errors next to the field they belong to. **[Review]**

```ts
readonly form = new FormGroup({
  query: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
});
```

## Accessibility (WCAG 2.2 AA)

Target: WCAG 2.2 AA for every page.

- Every form control has a visible label (`<label for>` or a `<label>` wrapper). Placeholders are not labels. **[Review; template a11y rules to be enabled]**
- Interactive elements are native (`<button>`, `<a href>`). Custom controls need a role, keyboard handling and focus. **[Review]**
- Focus is visible: do not remove `:focus-visible` outlines without a replacement. **[Review]**
- Async status (loading, saved, error, "N results") is announced with `aria-live="polite"` (errors with `role="alert"` when urgent). **[Review]**
- Colour contrast of at least 4.5:1 for text. Colour is never the only signal. **[Review]**

## Styling (SCSS and BEM)

- Class names follow BEM: `block`, `block__element`, `block--modifier`, `block__element--modifier`, each part kebab-case. One block per component, named after it (`status-page` → `.status`). **[Enforced: stylelint `selector-class-pattern`]**
- State is a modifier class, not a bare second class: `status__badge--down`, never `.badge.down`. Bind it with `[class.status__badge--down]="isDown()"`. **[Review]**
- Write elements and modifiers with `&__` / `&--` inside the block. Don't style tags or IDs: no `nav a`, `form`, `#main`. **[Enforced: `selector-no-qualifying-type`, `selector-max-id`, `selector-max-compound-selectors: 3`, `max-nesting-depth: 3`]**
- No `!important`; the one exception is the global reduced-motion override. **[Enforced: `declaration-no-important`]**
- Use design tokens (`var(--space-3)`, `var(--color-…)`) from `styles.scss`; no raw colours or spacing in components. **[Review]**
- Run `pnpm nx run web:lint-styles` (pre-commit runs stylelint with `--fix`).

```scss
// bad
.badge.down { … }
nav a.active { … }

// good
.status {
    &__badge {
        …
        &--down { … }
    }
}
```

## Performance budgets

Set in `apps/web/project.json` and checked by the Angular build. **[Enforced: Angular build budgets]**

| Budget | Warning | Error |
|--------|---------|-------|
| Initial bundle | 500 kB | 1 MB |
| Any component style | 4 kB | 8 kB |

- Lazy-load every feature route so the initial bundle stays small. **[Review]**
- Do not add a UI library or a charting library to the initial bundle without a PR note on size. **[Review]**
- Use `@defer` for heavy below-the-fold content. **[Review]**

## Testing

- Unit tests run with Vitest through the Angular unit-test builder (`@angular/build:unit-test`). Run them with `pnpm nx test web`. **[Enforced: `CI / js` (target)]**
- Test behaviour through the DOM and public inputs/outputs, not private fields or signal internals. **[Review]**
- HTTP: `provideHttpClientTesting()` and `HttpTestingController`. Verify the request URL, method and body, and flush a typed response. Always call `verify()` in `afterEach`. **[Review]**
- Cover the error path: the form shows the server error, and the status region announces it. **[Review]**

```ts
it('shows an error when the search request fails', () => {
  const fixture = TestBed.createComponent(SearchPageComponent);
  fixture.detectChanges();
  const http = TestBed.inject(HttpTestingController);

  fixture.componentInstance.search('lease');
  http.expectOne('/api/v1/search?q=lease').flush({ code: 'UNAVAILABLE' }, { status: 503, statusText: 'Service Unavailable' });
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector('[role="alert"]')).toBeTruthy();
  http.verify();
});
```

- End-to-end tests use Playwright in `apps/web-e2e`. Mock the API with `page.route('**/api/v1/**', ...)` so the e2e suite does not need the backend or AI services. **[Enforced: `CI / e2e-web` (target)]**
- Use role and label locators (`getByRole`, `getByLabel`). Do not use CSS class selectors. **[Review]**

## Security

- Never bind document content as HTML. Do not use `innerHTML`, `bypassSecurityTrust*`, or `[innerHtml]` with user or document text. Render text with interpolation. **[Review]**
- Document text is untrusted. Show it as text, and show citations as links only after the URL is built from ids, not from document content. **[Review]**
- The app ships under a Content-Security-Policy set by nginx. Do not add inline scripts or `unsafe-inline` styles. **[Review]**
- Do not store tokens in `localStorage`. Use the auth flow the backend defines (see [security.md](security.md)). **[Review]**
- Do not log document text or tokens from the browser. **[Review]**

## Checks to run locally

```bash
pnpm nx lint web
pnpm nx test web
pnpm nx build web
pnpm nx e2e web-e2e
```

---
name: angular-standards
description: How to write Angular code in docQA (apps/web). Covers small zoneless standalone components with signals, modern control flow, inject(), strict types, ng-elemental (El*) components, BEM SCSS, the ApiClient with @docqa/contracts models, accessibility and tests. Use whenever you create or change anything under apps/web, including components, templates, styles, services, routes and specs.
---

# Angular standards (apps/web)

Full rules: `docs/engineering/angular.md` and `docs/engineering/typescript.md`. This skill is the working checklist. **[Lint]** means a tool fails the build.

## Hard limits

| Rule | Limit |
| --- | --- |
| File size (`.ts`, `.html`, `.scss`) | ≤ 400 lines **[Lint]** |
| Function / method | ≤ 50 lines, complexity ≤ 10, nesting ≤ 4, ≤ 6 params **[Lint]** |
| Types | no `any` / `$any` **[Lint]**; every function has an explicit return type **[Lint]** |
| Template conditions | ≤ 4 boolean operands **[Lint]**: move logic to a `computed()` |

Near a limit? Split before you add code: child component, a `computed()`, a feature service, or a pure function in `*.utils.ts` with its own spec. Never raise a limit or add a disable comment to get past one.

## Component shape

```ts
@Component({
    selector: 'dq-document-list',              // dq- prefix, kebab-case [Lint]
    changeDetection: ChangeDetectionStrategy.OnPush, // [Lint]
    imports: [RouterLink],
    templateUrl: './document-list.html',
    styleUrl: './document-list.scss',
})
export class DocumentList {
    private readonly documents = inject(DocumentsService); // inject(), not ctor DI [Lint]
    readonly tenantId = input.required<Id>();               // input(), not @Input [Lint]
    readonly selected = output<DocumentSummary>();          // output(), not @Output [Lint]
    protected readonly items = signal<DocumentSummary[]>([]);
    protected readonly isEmpty = computed((): boolean => this.items().length === 0);

    protected select(doc: DocumentSummary): void {
        this.selected.emit(doc);
    }
}
```

- Standalone components only, the app is zoneless, and state lives in `signal`/`computed`/`linkedSignal`. Use `effect()` only for side effects.
- Templates: `@if` / `@for (…; track x.id)` / `@switch` / `@defer` **[Lint]**. Self-closing tags for empty components **[Lint]**. `NgOptimizedImage` for images **[Lint]**. Never call methods for derived values; use a `computed`.
- Members the template uses are `protected`; injected services are `private readonly`.
- Folders: `core/` (singletons, ApiClient, interceptors), `shared/` (presentational, no feature knowledge), `features/<name>/` (`routes.ts`, `pages/`, `components/`, `data/`). Features don't import other features.

## Types and data

- Payload and response types come from `@docqa/contracts` only (see the `shared-models` skill). Never redeclare an API shape in the web app.
- All HTTP goes through `core/api/ApiClient` with paths relative to `/api/v1`. Never inject `HttpClient` in a component, and never hardcode a host. Dev uses `apps/web/proxy.conf.json` (`/api` → :3000).
- Model UI state as a discriminated union: `type State = { kind: 'loading' } | { kind: 'loaded'; data: X } | { kind: 'error' }`.
- Parse unknown data to a contract type at the edge, and narrow `unknown`; don't cast.

## UI components: ng-elemental only

- All UI is built from ng-elemental (`El*`) components, copied into `libs/ui` by its CLI (`elemental.json` sets `componentsDir`). Don't hand-build a widget that ng-elemental has: button, input, label + form-error, alert, card, list, stack/container/grid, progress, dialog, toast, table, and so on.
- Find components with the ng-elemental MCP tools (`search_components`, `get_component`, `get_component_examples`); don't guess names or inputs. Read the guidelines (`get_guidelines`) before new UI.
- Add a component with `npx @ng-elemental/cli add <name>`; the user runs it. **Never edit files in `libs/ui`** and never copy component source by hand. It is vendored code, excluded from Prettier and Stylelint so `add --force` updates stay clean.
- Import by path alias and list each class in `imports`: `import { ElButton } from '@docqa/ui/button/button';`.
- Bind state with signals: `[(value)]="question"`, `[error]="error() !== null"`. Pair `el-label htmlFor` with the control's `inputId`, and show errors with `el-form-error`.
- Icons are `<el-icon name="circle-check" />` (Font Awesome names, no `fa-` prefix). No inline SVG or unicode glyphs.
- If ng-elemental has no component for the need (for example a textarea), ask before building one.

## Styling: BEM SCSS

- Page SCSS is for layout tweaks and page-specific states only; El* widgets bring their own styles. Don't restyle El* internals.
- One block per component, named after it. Elements are `block__element` and modifiers are `block--modifier` / `block__element--modifier`, all kebab-case **[Stylelint]**.
- Nest with `&__` / `&--`, at most 3 levels deep. No tag or ID selectors, no `!important` **[Stylelint]**.
- State is a modifier bound in the template: `[class.status__state--down]="!row.up"`, never `.state.down`.
- Use ng-elemental tokens (`var(--el-space-3)`, `var(--el-color-error)`, `var(--el-radius-md)`); no raw colours or spacing. Brand values change only in `libs/ui/theme/tokens.scss`. Typography classes come from ng-elemental (`el-text-h2`, `el-text-muted`).

```scss
.status {
    &__state {
        font-weight: 600;
        &--down { color: var(--el-color-error); }
    }
}
```

## Accessibility and tests

- WCAG 2.2 AA: label every control, keep focus visible, use `aria-live` for async status, keep contrast ≥ 4.5:1, and never use colour as the only signal **[Lint: template a11y set]**.
- Specs sit next to the code (`*.spec.ts`). Test behaviour through the DOM and inputs/outputs; mock HTTP with `HttpTestingController`. Query by role, label or BEM class (`el-list-item`, `input#question`).

## Before you finish

```bash
pnpm nx run-many -t lint lint-styles typecheck test -p web
pnpm nx build web            # budgets enforced
pnpm nx e2e web-e2e          # when UI flows changed
```

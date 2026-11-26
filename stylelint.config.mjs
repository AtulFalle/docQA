/**
 * SCSS rules for apps/web. Rationale: docs/engineering/angular.md#styling-scss-and-bem.
 * Class names follow BEM: block, block__element, block--modifier, block__element--modifier,
 * each part kebab-case (e.g. `status-card__title--muted`).
 */
const KEBAB = '[a-z][a-z0-9]*(?:-[a-z0-9]+)*';
const BEM = `^${KEBAB}(?:__${KEBAB})?(?:--${KEBAB})?$`;

export default {
    extends: ['stylelint-config-standard-scss'],
    // libs/ui is ng-elemental copy-in source (el-* BEM, upstream style); it is not edited by hand.
    ignoreFiles: [
        '**/dist/**',
        '**/coverage/**',
        '**/node_modules/**',
        '**/.angular/**',
        'libs/ui/**',
    ],
    rules: {
        'selector-class-pattern': [
            BEM,
            {
                resolveNestedSelectors: true,
                message: (selector) =>
                    `Class "${selector}" is not BEM (block__element--modifier, kebab-case)`,
            },
        ],
        // Flat BEM selectors: no IDs, no tag-qualified classes, shallow nesting.
        'selector-max-id': 0,
        'selector-no-qualifying-type': true,
        'selector-max-compound-selectors': 3,
        'max-nesting-depth': [3, { ignoreAtRules: ['media', 'supports', 'include'] }],
        'declaration-no-important': true,
        // Angular component hosts and view encapsulation.
        'selector-pseudo-class-no-unknown': [
            true,
            { ignorePseudoClasses: ['host', 'host-context'] },
        ],
        'selector-pseudo-element-no-unknown': [true, { ignorePseudoElements: ['ng-deep'] }],
    },
};

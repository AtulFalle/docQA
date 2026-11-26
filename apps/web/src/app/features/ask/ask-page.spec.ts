import { TestBed } from '@angular/core/testing';
import { AskPage } from './ask-page';

describe('AskPage', () => {
    function setup() {
        TestBed.configureTestingModule({ imports: [AskPage] });
        const fixture = TestBed.createComponent(AskPage);
        return { fixture, el: fixture.nativeElement as HTMLElement };
    }

    async function type(
        fixture: ReturnType<typeof setup>['fixture'],
        input: HTMLInputElement,
        value: string,
    ): Promise<void> {
        input.value = value;
        input.dispatchEvent(new Event('input'));
        await fixture.whenStable();
    }

    it('shows the M1 banner and a disabled submit button', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        expect(el.textContent).toContain('Answering is coming in M1 (query API)');
        expect((el.querySelector('button[type="submit"]') as HTMLButtonElement).disabled).toBe(
            true,
        );
    });

    it('has a labelled question input', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        expect(el.querySelector('label[for="question"]')).not.toBeNull();
        expect(el.querySelector('input#question')).not.toBeNull();
    });

    it('updates the counter and requires a question once touched', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        const input = el.querySelector('input#question') as HTMLInputElement;
        await type(fixture, input, 'hello');
        expect(el.querySelector('#counter')?.textContent).toContain('5 / 2000');
        expect(el.querySelector('[role="alert"]')).toBeNull();

        await type(fixture, input, '');
        input.dispatchEvent(new FocusEvent('focusout', { bubbles: true }));
        await fixture.whenStable();
        expect(el.querySelector('[role="alert"]')?.textContent).toContain(
            'Please enter a question',
        );
        expect(input.getAttribute('aria-invalid')).toBe('true');
    });

    it('flags questions over the length limit', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        await type(
            fixture,
            el.querySelector('input#question') as HTMLInputElement,
            'x'.repeat(2001),
        );
        expect(el.querySelector('[role="alert"]')?.textContent).toContain('under 2000 characters');
    });
});

import { TestBed } from '@angular/core/testing';
import { AskPage } from './ask-page';

describe('AskPage', () => {
    function setup() {
        TestBed.configureTestingModule({ imports: [AskPage] });
        const fixture = TestBed.createComponent(AskPage);
        return { fixture, el: fixture.nativeElement as HTMLElement };
    }

    it('shows the M1 banner and a disabled submit button', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        expect(el.textContent).toContain('Answering is coming in M1 (query API)');
        expect((el.querySelector('button[type="submit"]') as HTMLButtonElement).disabled).toBe(
            true,
        );
    });

    it('has a labelled textarea with maxlength 2000', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        const ta = el.querySelector('textarea') as HTMLTextAreaElement;
        expect(el.querySelector('label[for="question"]')).not.toBeNull();
        expect(ta.getAttribute('maxlength')).toBe('2000');
    });

    it('validates required and updates the counter', async () => {
        const { fixture, el } = setup();
        await fixture.whenStable();
        const ta = el.querySelector('textarea') as HTMLTextAreaElement;
        ta.value = 'hello';
        ta.dispatchEvent(new Event('input'));
        await fixture.whenStable();
        expect(el.querySelector('#counter')?.textContent).toContain('5 / 2000');
        ta.value = '';
        ta.dispatchEvent(new Event('input'));
        ta.dispatchEvent(new Event('blur'));
        await fixture.whenStable();
        expect(el.querySelector('[role="alert"]')?.textContent).toContain(
            'Please enter a question',
        );
    });
});

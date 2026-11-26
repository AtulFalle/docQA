import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { ElAlert } from '@docqa/ui/alert/alert';
import { ElButton } from '@docqa/ui/button/button';
import { ElFormError } from '@docqa/ui/form-error/form-error';
import { ElInput } from '@docqa/ui/input/input';
import { ElLabel } from '@docqa/ui/label/label';
import { ElStack } from '@docqa/ui/stack/stack';

export const MAX_QUESTION_LENGTH = 2000;

@Component({
    selector: 'dq-ask-page',
    imports: [ElAlert, ElButton, ElFormError, ElInput, ElLabel, ElStack],
    templateUrl: './ask-page.html',
    styleUrl: './ask-page.scss',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AskPage {
    protected readonly max = MAX_QUESTION_LENGTH;
    protected readonly question = signal('');
    protected readonly touched = signal(false);

    protected readonly length = computed(() => this.question().length);
    protected readonly error = computed((): string | null => {
        if (this.length() > this.max) return `Keep the question under ${this.max} characters.`;
        if (this.touched() && this.question().trim() === '') return 'Please enter a question.';
        return null;
    });
}

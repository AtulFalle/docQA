import { ChangeDetectionStrategy, Component } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { map } from 'rxjs';

export const MAX_QUESTION_LENGTH = 2000;

@Component({
    selector: 'dq-ask-page',
    imports: [ReactiveFormsModule],
    templateUrl: './ask-page.html',
    styleUrl: './ask-page.scss',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AskPage {
    protected readonly max = MAX_QUESTION_LENGTH;
    protected readonly form = new FormGroup({
        question: new FormControl('', {
            nonNullable: true,
            validators: [Validators.required, Validators.maxLength(MAX_QUESTION_LENGTH)],
        }),
    });
    protected readonly length = toSignal(
        this.form.controls.question.valueChanges.pipe(map((v) => v.length)),
        { initialValue: 0 },
    );
}

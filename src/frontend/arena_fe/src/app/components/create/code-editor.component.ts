import { AfterViewInit, ChangeDetectionStrategy, Component, ElementRef, OnDestroy, effect, input, output, signal, viewChild } from '@angular/core';
import type { EditorHandle } from './code-editor.setup';

/**
 * Python code editor backed by CodeMirror 6 (loaded lazily). Falls back to a plain textarea
 * until the editor chunk arrives, so the page is usable immediately.
 */
@Component({
  selector: 'arena-code-editor',
  standalone: true,
  template: `
    <div class="ce-frame" [class.is-ready]="ready()">
      <div #host class="ce-host"></div>
      @if (!ready()) {
        <textarea
          class="ce-fallback"
          spellcheck="false"
          [value]="value()"
          (input)="onFallbackInput($any($event.target).value)"
          aria-label="Automaton code"
        ></textarea>
      }
    </div>
    @if (!readOnly()) {
    <div class="ce-hints">
      <span><kbd>Tab</kbd> indent</span>
      <span><kbd>Shift</kbd>+<kbd>Tab</kbd> outdent</span>
      <span><kbd>Ctrl</kbd>+<kbd>F</kbd> find / replace</span>
      <span><kbd>Ctrl</kbd>+<kbd>Z</kbd> undo</span>
      <span><kbd>Ctrl</kbd>+<kbd>/</kbd> comment</span>
      <span><kbd>Ctrl</kbd>+<kbd>Space</kbd> complete</span>
    </div>
    }
  `,
  styles: `
    :host {
      display: block;
    }

    .ce-frame {
      position: relative;
      height: 480px;
      min-height: 240px;
      resize: vertical;
      overflow: hidden;
      border-radius: 12px;
      border: 1px solid rgba(78, 168, 255, 0.3);
      background: rgba(4, 9, 16, 0.95);
    }

    .ce-frame:focus-within {
      border-color: var(--accent-1);
    }

    .ce-host {
      height: 100%;
    }

    .ce-fallback {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      resize: none;
      border: 0;
      padding: 12px 14px;
      background: transparent;
      color: var(--ink-900);
      font-family: var(--font-mono);
      font-size: 0.84rem;
      line-height: 1.55;
      tab-size: 4;
      outline: none;
    }

    .ce-hints {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 16px;
      margin-top: 6px;
      color: var(--ink-500);
      font-size: 0.68rem;
    }

    .ce-hints kbd {
      display: inline-block;
      padding: 0 5px;
      border-radius: 4px;
      border: 1px solid rgba(78, 168, 255, 0.25);
      background: rgba(12, 22, 40, 0.8);
      font-family: var(--font-mono);
      font-size: 0.64rem;
      color: var(--ink-700);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaCodeEditorComponent implements AfterViewInit, OnDestroy {
  readonly value = input('');
  readonly readOnly = input(false);
  /** 1-based line to highlight as the error location; null clears it */
  readonly errorLine = input<number | null>(null);
  readonly valueChange = output<string>();

  readonly ready = signal(false);
  private readonly host = viewChild.required<ElementRef<HTMLDivElement>>('host');
  private editor: EditorHandle | null = null;
  private destroyed = false;
  /** last value emitted by the editor, so an echo from the parent does not reset the cursor */
  private lastEmitted: string | null = null;

  constructor() {
    effect(() => {
      const value = this.value();
      if (this.editor && value !== this.lastEmitted) {
        this.editor.setValue(value);
      }
      this.lastEmitted = null;
    });
    effect(() => {
      const flag = this.readOnly();
      this.editor?.setReadOnly(flag);
    });
    effect(() => {
      const line = this.errorLine();
      this.editor?.setErrorLine(line);
    });
  }

  ngAfterViewInit(): void {
    void this.mount(this.host().nativeElement);
  }

  private async mount(host: HTMLDivElement): Promise<void> {
    if (this.editor) {
      return;
    }
    const { createEditor } = await import('./code-editor.setup');
    if (this.destroyed || this.editor) {
      return;
    }
    this.editor = createEditor(host, this.value(), (next) => {
      this.lastEmitted = next;
      this.valueChange.emit(next);
    });
    this.editor.setReadOnly(this.readOnly());
    this.editor.setErrorLine(this.errorLine());
    this.ready.set(true);
  }

  onFallbackInput(next: string): void {
    this.lastEmitted = next;
    this.valueChange.emit(next);
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.editor?.destroy();
    this.editor = null;
  }
}

/**
 * CodeMirror 6 setup for the automaton editor. Kept in its own module and loaded with a dynamic
 * import so the editor bundle is a lazy chunk fetched only when the Create page mounts.
 */
import { EditorState, Compartment, StateEffect, StateField } from '@codemirror/state';
import { EditorView, Decoration, type DecorationSet, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection, rectangularSelection, crosshairCursor, highlightSpecialChars, dropCursor } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { bracketMatching, foldGutter, foldKeymap, indentOnInput, indentUnit, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap } from '@codemirror/autocomplete';
import { highlightSelectionMatches, searchKeymap } from '@codemirror/search';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';

export interface EditorHandle {
  getValue(): string;
  setValue(value: string): void;
  setReadOnly(readOnly: boolean): void;
  /** highlight a 1-based line (or clear with null) and scroll it into view */
  setErrorLine(line: number | null): void;
  focus(): void;
  destroy(): void;
}

const setErrorLineEffect = StateEffect.define<number | null>();
const errorLineDecoration = Decoration.line({ class: 'cm-error-line' });

/** one highlighted line; cleared automatically as soon as the document changes */
const errorLineField = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update(deco, tr) {
    if (tr.docChanged) {
      return Decoration.none;
    }
    for (const effect of tr.effects) {
      if (effect.is(setErrorLineEffect)) {
        if (effect.value === null) {
          return Decoration.none;
        }
        const n = Math.max(1, Math.min(tr.state.doc.lines, effect.value));
        return Decoration.set([errorLineDecoration.range(tr.state.doc.line(n).from)]);
      }
    }
    return deco;
  },
  provide: (field) => EditorView.decorations.from(field)
});

const arenaTheme = EditorView.theme(
  {
    '&': {
      height: '100%',
      fontSize: '0.84rem',
      backgroundColor: 'rgba(4, 9, 16, 0.95)',
      borderRadius: '12px'
    },
    '.cm-scroller': {
      fontFamily: 'var(--font-mono)',
      lineHeight: '1.55',
      overflow: 'auto'
    },
    '.cm-content': {
      padding: '12px 0'
    },
    '.cm-gutters': {
      backgroundColor: 'rgba(4, 9, 16, 0.95)',
      borderRight: '1px solid rgba(78, 168, 255, 0.14)',
      color: 'rgba(148, 163, 184, 0.7)'
    },
    '.cm-activeLineGutter': {
      backgroundColor: 'rgba(78, 168, 255, 0.12)'
    },
    '.cm-activeLine': {
      backgroundColor: 'rgba(78, 168, 255, 0.06)'
    },
    '&.cm-focused': {
      outline: 'none'
    },
    '.cm-selectionMatch': {
      backgroundColor: 'rgba(45, 212, 191, 0.2)'
    },
    '.cm-matchingBracket': {
      backgroundColor: 'rgba(45, 212, 191, 0.25)',
      outline: '1px solid rgba(45, 212, 191, 0.5)'
    },
    '.cm-tooltip': {
      backgroundColor: '#0c1628',
      border: '1px solid rgba(78, 168, 255, 0.3)'
    },
    '.cm-tooltip.cm-tooltip-autocomplete > ul > li[aria-selected]': {
      backgroundColor: 'rgba(78, 168, 255, 0.25)'
    },
    '.cm-panels': {
      backgroundColor: '#0c1628',
      color: 'inherit'
    },
    '.cm-panels.cm-panels-bottom': {
      borderTop: '1px solid rgba(78, 168, 255, 0.2)'
    },
    /* two classes so the red wins over .cm-activeLine when the caret sits on the error line */
    '.cm-line.cm-error-line': {
      backgroundColor: 'rgba(255, 111, 141, 0.16)',
      boxShadow: 'inset 3px 0 0 rgba(255, 111, 141, 0.9)'
    },
    '.cm-searchMatch': {
      backgroundColor: 'rgba(255, 209, 102, 0.3)'
    },
    '.cm-searchMatch.cm-searchMatch-selected': {
      backgroundColor: 'rgba(255, 209, 102, 0.6)'
    }
  },
  { dark: true }
);

export const createEditor = (parent: HTMLElement, initial: string, onChange: (value: string) => void): EditorHandle => {
  const readOnly = new Compartment();
  const state = EditorState.create({
    doc: initial,
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightSpecialChars(),
      history(),
      foldGutter(),
      drawSelection(),
      dropCursor(),
      EditorState.allowMultipleSelections.of(true),
      indentOnInput(),
      indentUnit.of('    '),
      EditorState.tabSize.of(4),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      bracketMatching(),
      closeBrackets(),
      autocompletion(),
      rectangularSelection(),
      crosshairCursor(),
      highlightActiveLine(),
      highlightSelectionMatches(),
      keymap.of([...closeBracketsKeymap, ...defaultKeymap, ...searchKeymap, ...historyKeymap, ...foldKeymap, ...completionKeymap, indentWithTab]),
      python(),
      // earlier extensions win, so the arena colors override One Dark's grey background
      arenaTheme,
      oneDark,
      readOnly.of(EditorState.readOnly.of(false)),
      errorLineField,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          onChange(update.state.doc.toString());
        }
      })
    ]
  });
  const view = new EditorView({ state, parent });
  return {
    getValue: () => view.state.doc.toString(),
    setValue: (value: string) => {
      const current = view.state.doc.toString();
      if (current !== value) {
        view.dispatch({ changes: { from: 0, to: current.length, insert: value } });
      }
    },
    setReadOnly: (flag: boolean) => {
      view.dispatch({ effects: readOnly.reconfigure(EditorState.readOnly.of(flag)) });
    },
    setErrorLine: (line: number | null) => {
      if (line === null) {
        view.dispatch({ effects: setErrorLineEffect.of(null) });
        return;
      }
      const n = Math.max(1, Math.min(view.state.doc.lines, line));
      const pos = view.state.doc.line(n).from;
      view.dispatch({ effects: [setErrorLineEffect.of(n), EditorView.scrollIntoView(pos, { y: 'center' })] });
    },
    focus: () => view.focus(),
    destroy: () => view.destroy()
  };
};

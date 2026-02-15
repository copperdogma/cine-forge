import { useEffect, useRef } from 'react'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { StreamLanguage } from '@codemirror/language'
import { searchKeymap } from '@codemirror/search'
import { keymap } from '@codemirror/view'
import { tags } from '@lezer/highlight'
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language'

// Dark theme matching app design tokens
const screenplayTheme = EditorView.theme(
  {
    '&': {
      color: 'oklch(0.985 0.002 247.86)',
      backgroundColor: 'oklch(0.145 0.014 285.82)',
      height: '100%',
      fontSize: '13px',
      fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
    },
    '.cm-content': {
      caretColor: 'oklch(0.985 0.002 247.86)',
      padding: '1rem',
      lineHeight: '1.6',
    },
    '&.cm-focused .cm-cursor': {
      borderLeftColor: 'oklch(0.985 0.002 247.86)',
    },
    '&.cm-focused .cm-selectionBackground, ::selection': {
      backgroundColor: 'oklch(0.269 0.015 285.82)',
    },
    '.cm-selectionBackground': {
      backgroundColor: 'oklch(0.269 0.015 285.82)',
    },
    '.cm-gutters': {
      backgroundColor: 'oklch(0.17 0.014 285.82)',
      color: 'oklch(0.556 0.018 285.82)',
      border: 'none',
      paddingRight: '0.75rem',
    },
    '.cm-activeLineGutter': {
      backgroundColor: 'oklch(0.2 0.014 285.82)',
    },
    '.cm-lineNumbers .cm-gutterElement': {
      minWidth: '3ch',
      textAlign: 'right',
    },
    '.cm-scroller': {
      overflow: 'auto',
      maxHeight: '600px',
    },
    '.cm-line': {
      padding: '0',
    },
  },
  { dark: true },
)

// Syntax highlighting for screenplay elements
const screenplayHighlighting = HighlightStyle.define([
  { tag: tags.heading, color: 'oklch(0.847 0.165 81.32)', fontWeight: 'bold' }, // Amber/orange for scene headings
  { tag: tags.character, color: 'oklch(0.764 0.186 254.32)' }, // Blue for character names
  { tag: tags.comment, color: 'oklch(0.556 0.018 285.82)', fontStyle: 'italic' }, // Muted for parentheticals
  { tag: tags.keyword, color: 'oklch(0.803 0.197 326.98)' }, // Purple for transitions
])

// Create a custom highlight extension
const screenplaySyntax = syntaxHighlighting(screenplayHighlighting)

export interface ScreenplayEditorProps {
  content: string
  readOnly?: boolean
}

export function ScreenplayEditor({ content, readOnly = true }: ScreenplayEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)

  useEffect(() => {
    if (!editorRef.current) return

    // Create editor state
    const state = EditorState.create({
      doc: content,
      extensions: [
        basicSetup,
        screenplayTheme,
        screenplaySyntax,
        StreamLanguage.define({
          token(stream) {
            const line = stream.string

            // Scene headings
            if (stream.sol()) {
              if (line.match(/^(INT\.|EXT\.|INT\/EXT\.|I\/E\.)/i)) {
                stream.skipToEnd()
                return 'heading'
              }

              // Transitions
              if (line.match(/^(FADE|CUT|DISSOLVE|MATCH CUT)/i) || line.match(/TO:\s*$/)) {
                stream.skipToEnd()
                return 'transition'
              }

              // Character names
              const trimmed = line.trim()
              if (
                trimmed === trimmed.toUpperCase() &&
                trimmed.length > 0 &&
                trimmed.length < 30 &&
                !trimmed.match(/^(INT\.|EXT\.|INT\/EXT\.|I\/E\.)/i) &&
                !trimmed.match(/[.:]$/)
              ) {
                stream.skipToEnd()
                return 'character'
              }

              // Parentheticals
              if (line.match(/^\s*\([^)]*\)\s*$/)) {
                stream.skipToEnd()
                return 'parenthetical'
              }
            }

            stream.skipToEnd()
            return null
          },
        }),
        keymap.of(searchKeymap),
        EditorView.lineWrapping,
        EditorState.readOnly.of(readOnly),
        EditorView.editable.of(!readOnly),
      ],
    })

    // Create editor view
    const view = new EditorView({
      state,
      parent: editorRef.current,
    })

    viewRef.current = view

    // Cleanup on unmount
    return () => {
      view.destroy()
      viewRef.current = null
    }
  }, [content, readOnly])

  return <div ref={editorRef} className="screenplay-editor rounded-md border border-border overflow-hidden" />
}

// Default export for lazy loading
export default ScreenplayEditor

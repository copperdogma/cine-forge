import { useEffect, useRef, useImperativeHandle, forwardRef, useCallback } from 'react'
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

export interface ScreenplayEditorHandle {
  /** Scroll to a 1-indexed line number */
  scrollToLine: (line: number) => void
  /** Find the first line matching a scene heading pattern and scroll to it */
  scrollToHeading: (heading: string) => void
}

export interface ScreenplayEditorProps {
  content: string
  readOnly?: boolean
  /** Called when a scene heading line is clicked. Receives the heading text. */
  onSceneHeadingClick?: (heading: string) => void
}

const isSceneHeading = (line: string) => /^(INT\.|EXT\.|INT\/EXT\.|I\/E\.)/i.test(line)

export const ScreenplayEditor = forwardRef<ScreenplayEditorHandle, ScreenplayEditorProps>(
  function ScreenplayEditor({ content, readOnly = true, onSceneHeadingClick }, ref) {
    const editorRef = useRef<HTMLDivElement>(null)
    const viewRef = useRef<EditorView | null>(null)
    const onClickRef = useRef(onSceneHeadingClick)
    
    useEffect(() => {
      onClickRef.current = onSceneHeadingClick
    }, [onSceneHeadingClick])

    useImperativeHandle(ref, () => ({
      scrollToLine(lineNumber: number) {
        const view = viewRef.current
        if (!view) return
        const maxLines = view.state.doc.lines
        const clampedLine = Math.max(1, Math.min(lineNumber, maxLines))
        const pos = view.state.doc.line(clampedLine).from
        view.dispatch({
          effects: EditorView.scrollIntoView(pos, { y: 'start', yMargin: 50 }),
        })
      },
      scrollToHeading(heading: string) {
        const view = viewRef.current
        if (!view) return
        const norm = heading.toLowerCase().replace(/[^a-z0-9]/g, '')
        for (let i = 1; i <= view.state.doc.lines; i++) {
          const lineText = view.state.doc.line(i).text
          if (isSceneHeading(lineText)) {
            const lineNorm = lineText.toLowerCase().replace(/[^a-z0-9]/g, '')
            if (lineNorm.includes(norm) || norm.includes(lineNorm)) {
              const pos = view.state.doc.line(i).from
              view.dispatch({
                effects: EditorView.scrollIntoView(pos, { y: 'start', yMargin: 50 }),
              })
              return
            }
          }
        }
      },
    }))

    // Click handler for scene headings
    const handleClick = useCallback((view: EditorView, pos: number) => {
      if (!onClickRef.current) return false
      const line = view.state.doc.lineAt(pos)
      if (isSceneHeading(line.text)) {
        onClickRef.current(line.text)
        return true
      }
      return false
    }, [])

    useEffect(() => {
      if (!editorRef.current) return

      const state = EditorState.create({
        doc: content,
        extensions: [
          basicSetup,
          screenplayTheme,
          screenplaySyntax,
          StreamLanguage.define({
            token(stream) {
              const line = stream.string

              if (stream.sol()) {
                if (isSceneHeading(line)) {
                  stream.skipToEnd()
                  return 'heading'
                }

                if (line.match(/^(FADE|CUT|DISSOLVE|MATCH CUT)/i) || line.match(/TO:\s*$/)) {
                  stream.skipToEnd()
                  return 'transition'
                }

                const trimmed = line.trim()
                if (
                  trimmed === trimmed.toUpperCase() &&
                  trimmed.length > 0 &&
                  trimmed.length < 30 &&
                  !isSceneHeading(trimmed) &&
                  !trimmed.match(/[.:]$/)
                ) {
                  stream.skipToEnd()
                  return 'character'
                }

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
          // Make scene headings clickable with cursor pointer
          EditorView.domEventHandlers({
            click(event, view) {
              const pos = view.posAtCoords({ x: event.clientX, y: event.clientY })
              if (pos != null) return handleClick(view, pos)
              return false
            },
          }),
          // Style scene heading lines with pointer cursor when callback is set
          EditorView.theme({
            '.cm-line:has(.tok-heading)': {
              cursor: 'pointer',
            },
          }),
        ],
      })

      const view = new EditorView({
        state,
        parent: editorRef.current,
      })

      viewRef.current = view

      return () => {
        view.destroy()
        viewRef.current = null
      }
    }, [content, readOnly, handleClick])

    return <div ref={editorRef} className="screenplay-editor h-full overflow-hidden" />
  },
)

// Default export for lazy loading
export default ScreenplayEditor

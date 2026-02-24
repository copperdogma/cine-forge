import { useEffect, useRef, useImperativeHandle, forwardRef, useCallback } from 'react'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState, StateEffect, StateField } from '@codemirror/state'
import type { Range } from '@codemirror/state'
import { Decoration, WidgetType } from '@codemirror/view'
import type { DecorationSet } from '@codemirror/view'
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
    '.cm-scene-divider': {
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '0.2rem 1rem',
      borderTop: '1px solid oklch(0.28 0.015 285.82)',
      backgroundColor: 'oklch(0.165 0.013 285.82)',
      cursor: 'pointer',
      userSelect: 'none',
      transition: 'background-color 0.12s ease',
    },
    '.cm-scene-divider:hover': {
      backgroundColor: 'oklch(0.24 0.015 285.82)',
    },
    '.cm-scene-divider:hover .cm-scene-divider-label': {
      color: 'oklch(0.847 0.165 81.32)',
    },
    '.cm-scene-divider:hover .cm-scene-divider-arrow': {
      color: 'oklch(0.75 0.12 81.32)',
    },
    '.cm-scene-divider-label': {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.375rem',
      fontSize: '11px',
      fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
      color: 'oklch(0.55 0.06 81.32)',
      letterSpacing: '0.02em',
      lineHeight: '1.6',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      maxWidth: '80ch',
      transition: 'color 0.12s ease',
    },
    '.cm-scene-divider-arrow': {
      fontSize: '10px',
      color: 'oklch(0.40 0.015 285.82)',
      marginLeft: 'auto',
      flexShrink: '0',
      transition: 'color 0.12s ease',
    },
    '.cm-heading-line': {
      cursor: 'pointer',
      transition: 'background-color 0.12s ease',
    },
    '.cm-heading-line:hover': {
      backgroundColor: 'oklch(0.21 0.018 81.32)',
    },
    '.cm-character-line': {
      cursor: 'pointer',
      transition: 'background-color 0.12s ease',
    },
    '.cm-character-line:hover': {
      backgroundColor: 'oklch(0.21 0.018 254.32)',
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

const screenplaySyntax = syntaxHighlighting(screenplayHighlighting)

// --- Line type helpers (used by both decorations and click handlers) ---

const isSceneHeading = (line: string) => /^(INT\.|EXT\.|INT\/EXT\.|I\/E\.)/i.test(line)

const isCharacterLine = (line: string) => {
  const trimmed = line.trim()
  return (
    trimmed.length > 0 &&
    trimmed.length <= 40 &&
    trimmed === trimmed.toUpperCase() &&
    !isSceneHeading(trimmed) &&
    !/[.:]$/.test(trimmed) &&
    !/^(FADE|CUT|DISSOLVE|MATCH CUT)/i.test(trimmed)
  )
}

// --- Scene divider decoration ---

export interface SceneDividerData {
  entityId: string
  heading: string
  sceneNumber: number
  startLine: number
}

class SceneDividerWidget extends WidgetType {
  sceneNumber: number
  heading: string
  entityId: string

  constructor(sceneNumber: number, heading: string, entityId: string) {
    super()
    this.sceneNumber = sceneNumber
    this.heading = heading
    this.entityId = entityId
  }

  eq(other: SceneDividerWidget) {
    return (
      other.sceneNumber === this.sceneNumber &&
      other.heading === this.heading &&
      other.entityId === this.entityId
    )
  }

  toDOM() {
    const bar = document.createElement('div')
    bar.className = 'cm-scene-divider'
    bar.dataset.entityId = this.entityId

    const label = document.createElement('span')
    label.className = 'cm-scene-divider-label'
    label.textContent = `Scene ${this.sceneNumber}`

    const arrow = document.createElement('span')
    arrow.className = 'cm-scene-divider-arrow'
    arrow.textContent = '↗'

    bar.appendChild(label)
    bar.appendChild(arrow)
    return bar
  }
  // ignoreEvent not overridden: default false = clicks propagate to domEventHandlers
}

const setScenesEffect = StateEffect.define<SceneDividerData[]>()

const sceneDividersField = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update(deco, tr) {
    deco = deco.map(tr.changes)
    for (const e of tr.effects) {
      if (e.is(setScenesEffect)) {
        const lineCount = tr.state.doc.lines
        const seen = new Set<number>()
        const ranges: Range<Decoration>[] = []

        for (const scene of e.value) {
          if (scene.startLine < 1 || scene.startLine > lineCount) continue
          const pos = tr.state.doc.line(scene.startLine).from
          if (seen.has(pos)) continue
          seen.add(pos)
          ranges.push(
            Decoration.widget({
              widget: new SceneDividerWidget(scene.sceneNumber, scene.heading, scene.entityId),
              side: -1,
              block: true,
            }).range(pos),
          )
        }

        ranges.sort((a, b) => a.from - b.from)
        return ranges.length > 0 ? Decoration.set(ranges) : Decoration.none
      }
    }
    return deco
  },
  provide: f => EditorView.decorations.from(f),
})

// Stamp .cm-heading-line / .cm-character-line directly on .cm-line elements
// so CSS :hover can target them reliably (HighlightStyle uses opaque ͼN classes)
const headingLineDeco = Decoration.line({ class: 'cm-heading-line' })
const characterLineDeco = Decoration.line({ class: 'cm-character-line' })

function buildLineClassDecorations(state: EditorState): DecorationSet {
  const ranges: Range<Decoration>[] = []
  for (let i = 1; i <= state.doc.lines; i++) {
    const line = state.doc.line(i)
    if (isSceneHeading(line.text)) {
      ranges.push(headingLineDeco.range(line.from))
    } else if (isCharacterLine(line.text)) {
      ranges.push(characterLineDeco.range(line.from))
    }
  }
  return ranges.length > 0 ? Decoration.set(ranges) : Decoration.none
}

const lineClassField = StateField.define<DecorationSet>({
  create: state => buildLineClassDecorations(state),
  update(deco, tr) {
    if (!tr.docChanged) return deco
    return buildLineClassDecorations(tr.state)
  },
  provide: f => EditorView.decorations.from(f),
})

// --- Component ---

export interface ScreenplayEditorHandle {
  /** Scroll to a 1-indexed line number */
  scrollToLine: (line: number) => void
  /** Find the first line matching a scene heading pattern and scroll to it */
  scrollToHeading: (heading: string) => void
}

export interface ScreenplayEditorProps {
  content: string
  readOnly?: boolean
  /** Scene divider data — injected as block decorations between lines */
  scenes?: SceneDividerData[]
  /** Called when a scene heading line is clicked. Receives the heading text. */
  onSceneHeadingClick?: (heading: string) => void
  /** Called when a character name line (ALL CAPS) is clicked. Receives the character name. */
  onCharacterNameClick?: (name: string) => void
  /** Called when a scene divider bar is clicked. Receives the scene entityId. */
  onSceneDividerClick?: (entityId: string) => void
}

export const ScreenplayEditor = forwardRef<ScreenplayEditorHandle, ScreenplayEditorProps>(
  function ScreenplayEditor(
    { content, readOnly = true, scenes, onSceneHeadingClick, onCharacterNameClick, onSceneDividerClick },
    ref,
  ) {
    const editorRef = useRef<HTMLDivElement>(null)
    const viewRef = useRef<EditorView | null>(null)
    const onClickRef = useRef(onSceneHeadingClick)
    const onCharacterNameClickRef = useRef(onCharacterNameClick)
    const onSceneDividerClickRef = useRef(onSceneDividerClick)

    useEffect(() => { onClickRef.current = onSceneHeadingClick }, [onSceneHeadingClick])
    useEffect(() => { onCharacterNameClickRef.current = onCharacterNameClick }, [onCharacterNameClick])
    useEffect(() => { onSceneDividerClickRef.current = onSceneDividerClick }, [onSceneDividerClick])

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

    const handleClick = useCallback((view: EditorView, pos: number) => {
      const line = view.state.doc.lineAt(pos)
      if (isSceneHeading(line.text) && onClickRef.current) {
        onClickRef.current(line.text)
        return true
      }
      if (isCharacterLine(line.text) && onCharacterNameClickRef.current) {
        // Strip trailing parentheticals: "ROSE (O.S.)" → "ROSE"
        const name = line.text.trim().replace(/\s*\([^)]*\)\s*$/, '').trim()
        onCharacterNameClickRef.current(name)
        return true
      }
      return false
    }, [])

    // Create/recreate editor when content changes
    useEffect(() => {
      if (!editorRef.current) return

      const state = EditorState.create({
        doc: content,
        extensions: [
          basicSetup,
          screenplayTheme,
          screenplaySyntax,
          sceneDividersField,
          lineClassField,
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
          EditorView.domEventHandlers({
            click(event, view) {
              // Scene heading or character name click (text lines only)
              // Note: block widget clicks never reach domEventHandlers — WidgetType.ignoreEvent defaults to true,
              // causing CodeMirror to skip event processing for widgets. Those are handled by React onClick below.
              const pos = view.posAtCoords({ x: event.clientX, y: event.clientY })
              if (pos != null) return handleClick(view, pos)
              return false
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

    // Dispatch scene dividers whenever the scenes prop changes, without recreating the view
    useEffect(() => {
      const view = viewRef.current
      if (!view) return
      const dividers = (scenes ?? []).filter(s => s.startLine > 0)
      view.dispatch({ effects: setScenesEffect.of(dividers) })
    }, [scenes])

    return (
      <div
        ref={editorRef}
        className="screenplay-editor h-full overflow-hidden"
        onClick={(e) => {
          // Scene divider clicks bubble up here because WidgetType.ignoreEvent defaults true,
          // so CodeMirror never handles them — they fall through to the React wrapper naturally.
          const target = e.target as HTMLElement
          const divider = target.closest('.cm-scene-divider') as HTMLElement | null
          if (divider?.dataset.entityId) {
            onSceneDividerClickRef.current?.(divider.dataset.entityId)
          }
        }}
      />
    )
  },
)

// Default export for lazy loading
export default ScreenplayEditor

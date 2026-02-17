import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'

type ThemeId = 'obsidian' | 'ember' | 'slate' | 'noir'

const themes: Record<ThemeId, {
  name: string
  description: string
  vars: Record<string, string>
}> = {
  obsidian: {
    name: 'Obsidian',
    description: 'Cool dark with blue-steel accents — Linear-inspired',
    vars: {
      '--background': 'oklch(0.13 0.005 260)',
      '--foreground': 'oklch(0.93 0.01 260)',
      '--card': 'oklch(0.17 0.008 260)',
      '--card-foreground': 'oklch(0.93 0.01 260)',
      '--popover': 'oklch(0.17 0.008 260)',
      '--popover-foreground': 'oklch(0.93 0.01 260)',
      '--primary': 'oklch(0.65 0.15 250)',
      '--primary-foreground': 'oklch(0.98 0 0)',
      '--secondary': 'oklch(0.22 0.01 260)',
      '--secondary-foreground': 'oklch(0.88 0.01 260)',
      '--muted': 'oklch(0.22 0.01 260)',
      '--muted-foreground': 'oklch(0.6 0.02 260)',
      '--accent': 'oklch(0.25 0.02 250)',
      '--accent-foreground': 'oklch(0.88 0.01 260)',
      '--destructive': 'oklch(0.65 0.2 25)',
      '--border': 'oklch(0.28 0.01 260)',
      '--input': 'oklch(0.22 0.01 260)',
      '--ring': 'oklch(0.65 0.15 250)',
    },
  },
  ember: {
    name: 'Ember',
    description: 'Warm dark with amber/copper accents — Frame.io-inspired',
    vars: {
      '--background': 'oklch(0.14 0.008 55)',
      '--foreground': 'oklch(0.92 0.02 75)',
      '--card': 'oklch(0.18 0.01 55)',
      '--card-foreground': 'oklch(0.92 0.02 75)',
      '--popover': 'oklch(0.18 0.01 55)',
      '--popover-foreground': 'oklch(0.92 0.02 75)',
      '--primary': 'oklch(0.72 0.16 55)',
      '--primary-foreground': 'oklch(0.15 0.01 55)',
      '--secondary': 'oklch(0.23 0.015 55)',
      '--secondary-foreground': 'oklch(0.88 0.02 75)',
      '--muted': 'oklch(0.23 0.015 55)',
      '--muted-foreground': 'oklch(0.6 0.03 55)',
      '--accent': 'oklch(0.26 0.025 55)',
      '--accent-foreground': 'oklch(0.88 0.02 75)',
      '--destructive': 'oklch(0.65 0.2 25)',
      '--border': 'oklch(0.28 0.02 55)',
      '--input': 'oklch(0.22 0.015 55)',
      '--ring': 'oklch(0.72 0.16 55)',
    },
  },
  slate: {
    name: 'Slate',
    description: 'Neutral dark with sage/teal accents — Arc Studio-inspired',
    vars: {
      '--background': 'oklch(0.14 0.005 180)',
      '--foreground': 'oklch(0.92 0.01 180)',
      '--card': 'oklch(0.18 0.008 180)',
      '--card-foreground': 'oklch(0.92 0.01 180)',
      '--popover': 'oklch(0.18 0.008 180)',
      '--popover-foreground': 'oklch(0.92 0.01 180)',
      '--primary': 'oklch(0.68 0.12 175)',
      '--primary-foreground': 'oklch(0.98 0 0)',
      '--secondary': 'oklch(0.22 0.01 180)',
      '--secondary-foreground': 'oklch(0.88 0.01 180)',
      '--muted': 'oklch(0.22 0.01 180)',
      '--muted-foreground': 'oklch(0.58 0.02 180)',
      '--accent': 'oklch(0.25 0.02 175)',
      '--accent-foreground': 'oklch(0.88 0.01 180)',
      '--destructive': 'oklch(0.65 0.2 25)',
      '--border': 'oklch(0.28 0.01 180)',
      '--input': 'oklch(0.22 0.01 180)',
      '--ring': 'oklch(0.68 0.12 175)',
    },
  },
  noir: {
    name: 'Noir',
    description: 'Deep blacks with gold accents — premium cinema feel',
    vars: {
      '--background': 'oklch(0.11 0.005 85)',
      '--foreground': 'oklch(0.90 0.02 85)',
      '--card': 'oklch(0.15 0.008 85)',
      '--card-foreground': 'oklch(0.90 0.02 85)',
      '--popover': 'oklch(0.15 0.008 85)',
      '--popover-foreground': 'oklch(0.90 0.02 85)',
      '--primary': 'oklch(0.78 0.15 85)',
      '--primary-foreground': 'oklch(0.13 0.01 85)',
      '--secondary': 'oklch(0.20 0.01 85)',
      '--secondary-foreground': 'oklch(0.85 0.02 85)',
      '--muted': 'oklch(0.20 0.01 85)',
      '--muted-foreground': 'oklch(0.55 0.02 85)',
      '--accent': 'oklch(0.23 0.02 85)',
      '--accent-foreground': 'oklch(0.85 0.02 85)',
      '--destructive': 'oklch(0.65 0.2 25)',
      '--border': 'oklch(0.25 0.015 85)',
      '--input': 'oklch(0.20 0.01 85)',
      '--ring': 'oklch(0.78 0.15 85)',
    },
  },
}

// Artifact type colors for the color system preview
const artifactColors: Array<{ name: string; color: string; icon: string }> = [
  { name: 'Script', color: 'oklch(0.7 0.15 250)', icon: '📜' },
  { name: 'Scene', color: 'oklch(0.7 0.15 145)', icon: '🎬' },
  { name: 'Character', color: 'oklch(0.7 0.15 30)', icon: '👤' },
  { name: 'Location', color: 'oklch(0.7 0.15 175)', icon: '📍' },
  { name: 'Prop', color: 'oklch(0.7 0.12 55)', icon: '🔧' },
  { name: 'Config', color: 'oklch(0.6 0.1 290)', icon: '⚙️' },
]

function applyTheme(themeId: ThemeId) {
  // Must target the .dark element, not :root — the .dark CSS block
  // in index.css overrides :root variables due to higher specificity.
  const darkEl = document.querySelector('.dark') as HTMLElement | null
  if (!darkEl) return
  const theme = themes[themeId]
  for (const [key, value] of Object.entries(theme.vars)) {
    darkEl.style.setProperty(key, value)
  }
}

export default function ThemeShowcase() {
  const [activeTheme, setActiveTheme] = useState<ThemeId>('slate')

  function selectTheme(id: ThemeId) {
    setActiveTheme(id)
    applyTheme(id)
  }

  return (
    <div className="min-h-screen p-8 space-y-10">
      {/* Theme switcher */}
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold tracking-tight mb-2">CineForge — Visual Identity</h1>
        <p className="text-muted-foreground mb-6">Pick a theme direction. We'll iterate from there.</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(Object.entries(themes) as Array<[ThemeId, typeof themes[ThemeId]]>).map(([id, theme]) => (
            <button
              key={id}
              onClick={() => selectTheme(id)}
              className={`rounded-lg border p-3 text-left transition-all ${
                activeTheme === id
                  ? 'border-primary bg-primary/10 ring-2 ring-primary/30'
                  : 'border-border hover:border-primary/40'
              }`}
            >
              <span className="font-semibold text-sm">{theme.name}</span>
              <p className="text-xs text-muted-foreground mt-1">{theme.description}</p>
            </button>
          ))}
        </div>
      </div>

      <Separator className="max-w-4xl mx-auto" />

      {/* Typography */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Typography</h2>
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">The Screenplay Pipeline</h1>
          <h2 className="text-2xl font-semibold">Scene 14 — INT. WAREHOUSE — NIGHT</h2>
          <h3 className="text-xl font-medium">Character Bible: SARAH CHEN</h3>
          <p className="text-base text-foreground">
            The canonical script has been normalized and 47 scenes extracted. Three characters require attention in the review queue.
          </p>
          <p className="text-sm text-muted-foreground">
            Produced by screenplay_intake v1.2 · Claude Sonnet 4.5 · $0.024 · 3.2s
          </p>
        </div>
      </section>

      <Separator className="max-w-4xl mx-auto" />

      {/* Buttons */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Buttons</h2>
        <div className="flex flex-wrap gap-3">
          <Button>Run Pipeline</Button>
          <Button variant="secondary">View Artifacts</Button>
          <Button variant="outline">Export</Button>
          <Button variant="ghost">Cancel</Button>
          <Button variant="destructive">Delete Project</Button>
          <Button size="sm">Approve</Button>
          <Button size="sm" variant="outline">Regenerate</Button>
        </div>
      </section>

      <Separator className="max-w-4xl mx-auto" />

      {/* Badges */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Status Badges</h2>
        <div className="flex flex-wrap gap-3">
          <Badge>Healthy</Badge>
          <Badge variant="secondary">Running</Badge>
          <Badge variant="outline">Draft</Badge>
          <Badge variant="destructive">Failed</Badge>
          <Badge className="bg-amber-600/20 text-amber-400 border-amber-600/30">Stale</Badge>
          <Badge className="bg-blue-600/20 text-blue-400 border-blue-600/30">Needs Review</Badge>
          <Badge className="bg-purple-600/20 text-purple-400 border-purple-600/30">AI Generated</Badge>
          <Badge className="bg-emerald-600/20 text-emerald-400 border-emerald-600/30">User Edited</Badge>
        </div>
      </section>

      <Separator className="max-w-4xl mx-auto" />

      {/* Cards */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Cards & Artifact Previews</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">📜</span>
                <CardTitle className="text-base">Canonical Script</CardTitle>
              </div>
              <CardDescription>v3 · Healthy · screenplay_document</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">47 scenes · 12,340 words · Last updated 2 min ago</p>
              <div className="flex gap-2 mt-3">
                <Badge>Healthy</Badge>
                <Badge className="bg-purple-600/20 text-purple-400 border-purple-600/30">AI</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">👤</span>
                <CardTitle className="text-base">Character Bible</CardTitle>
              </div>
              <CardDescription>v1 · Needs Review · bible_manifest</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">8 characters · 3 flagged for review</p>
              <div className="flex gap-2 mt-3">
                <Badge className="bg-blue-600/20 text-blue-400 border-blue-600/30">Needs Review</Badge>
                <Badge className="bg-purple-600/20 text-purple-400 border-purple-600/30">AI</Badge>
              </div>
            </CardContent>
          </Card>

          <Card className="border-amber-600/30">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">📍</span>
                <CardTitle className="text-base">Location Bible</CardTitle>
                <Badge className="bg-amber-600/20 text-amber-400 border-amber-600/30 text-xs">Stale</Badge>
              </div>
              <CardDescription>v2 · Stale · bible_manifest</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">12 locations · Script updated since last extraction</p>
              <div className="flex gap-2 mt-3">
                <Button size="sm" variant="outline">Regenerate</Button>
                <Button size="sm" variant="ghost">Keep</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <Separator className="max-w-4xl mx-auto" />

      {/* Inputs */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Inputs</h2>
        <div className="max-w-md space-y-3">
          <Input placeholder="Search artifacts..." />
          <Input placeholder="Project name" defaultValue="My Feature Film" />
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-muted-foreground text-sm">Drop your screenplay here</p>
            <p className="text-xs text-muted-foreground mt-1">.fountain, .fdx, .pdf, .docx</p>
          </div>
        </div>
      </section>

      <Separator className="max-w-4xl mx-auto" />

      {/* Artifact type colors */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Artifact Type Colors</h2>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {artifactColors.map((a) => (
            <div
              key={a.name}
              className="rounded-lg border border-border p-3 text-center"
            >
              <div
                className="w-8 h-8 rounded-md mx-auto mb-2"
                style={{ backgroundColor: a.color }}
              />
              <span className="text-xs mr-1">{a.icon}</span>
              <span className="text-sm font-medium">{a.name}</span>
            </div>
          ))}
        </div>
      </section>

      <Separator className="max-w-4xl mx-auto" />

      {/* Three-panel skeleton */}
      <section className="max-w-6xl mx-auto space-y-4">
        <h2 className="text-xl font-semibold text-muted-foreground uppercase tracking-wider text-sm">Layout Skeleton</h2>
        <div className="rounded-lg border border-border overflow-hidden" style={{ height: 400 }}>
          {/* Top bar */}
          <div className="h-12 border-b border-border flex items-center px-4 gap-4">
            <span className="font-semibold text-sm">CineForge</span>
            <span className="text-muted-foreground text-sm">My Feature Film</span>
            <div className="flex-1" />
            <Badge variant="secondary" className="text-xs">3 items</Badge>
            <span className="text-xs text-muted-foreground">Inbox</span>
          </div>
          <div className="flex" style={{ height: 'calc(100% - 48px)' }}>
            {/* Navigator */}
            <div className="w-56 border-r border-border p-3 space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Navigator</p>
              {['Scenes', 'Characters', 'Locations', 'Props', 'Pipeline'].map((item) => (
                <div key={item} className="rounded-md px-2 py-1.5 text-sm hover:bg-accent cursor-pointer">
                  {item}
                </div>
              ))}
            </div>
            {/* Content canvas */}
            <div className="flex-1 p-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Content Canvas</p>
              <div className="grid grid-cols-3 gap-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="rounded-md bg-muted/50 h-20 animate-pulse" />
                ))}
              </div>
            </div>
            {/* Inspector */}
            <div className="w-64 border-l border-border p-3 space-y-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Inspector</p>
              <div className="space-y-2">
                <div className="rounded-md bg-muted/50 h-4 w-3/4" />
                <div className="rounded-md bg-muted/50 h-4 w-1/2" />
                <div className="rounded-md bg-muted/50 h-4 w-2/3" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="h-16" />
    </div>
  )
}

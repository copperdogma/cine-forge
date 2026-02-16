import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, Plus, Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useCreateProject } from '@/lib/hooks'
import { uploadProjectInput, previewSlug } from '@/lib/api'

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'project'
}

export default function NewProject() {
  const navigate = useNavigate()
  const [projectName, setProjectName] = useState('')
  const [slug, setSlug] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isNaming, setIsNaming] = useState(false)
  const [nameSource, setNameSource] = useState<'ai' | 'user' | 'filename'>('filename')

  const createProject = useCreateProject()

  const generateSlugFromContent = useCallback(async (file: File) => {
    setIsNaming(true)
    try {
      // Read first 2000 chars of the file for LLM analysis
      const text = await file.text()
      const snippet = text.slice(0, 2000)
      const result = await previewSlug(snippet, file.name)
      setProjectName(result.display_name)
      setSlug(result.slug)
      setNameSource('ai')
    } catch {
      // LLM failed — fall back to filename-based naming
      const fallbackName = cleanFilename(file.name)
      setProjectName(fallbackName)
      setSlug(slugify(fallbackName))
      setNameSource('filename')
    } finally {
      setIsNaming(false)
    }
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    const validFile = files.find(f =>
      /\.(pdf|fdx|fountain|txt|md|docx)$/i.test(f.name)
    )

    if (validFile) {
      setSelectedFile(validFile)
      generateSlugFromContent(validFile)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
      generateSlugFromContent(files[0])
    }
  }

  const handleNameChange = (value: string) => {
    setProjectName(value)
    setSlug(slugify(value))
    setNameSource('user')
  }

  const handleCreate = async () => {
    if (!selectedFile || !slug) return

    try {
      setIsUploading(true)

      // Step 1: Create the project with slug
      const project = await createProject.mutateAsync({
        slug,
        displayName: projectName.trim(),
      })

      // Step 2: Upload the input file
      await uploadProjectInput(project.project_id, selectedFile)

      // Step 3: Navigate to the new project
      toast.success('Project created successfully')
      navigate(`/${project.project_id}`)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create project'
      toast.error(message)
    } finally {
      setIsUploading(false)
    }
  }

  const canCreate = projectName.trim() !== '' && slug !== '' && selectedFile !== null && !isNaming
  const isProcessing = createProject.isPending || isUploading

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="text-2xl">New Project</CardTitle>
          <CardDescription>
            Create a new CineForge project from a screenplay
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Screenplay Upload */}
          <div className="space-y-2">
            <label htmlFor="screenplay-upload" className="text-sm font-medium">
              Screenplay
            </label>
            <div
              role="button"
              tabIndex={0}
              aria-label={selectedFile ? `Selected file: ${selectedFile.name}. Press Enter to change file` : "Drop screenplay here or press Enter to browse files"}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  document.getElementById('screenplay-upload')?.click()
                }
              }}
              className={cn(
                "relative flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors",
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-muted-foreground/50",
                selectedFile && "border-primary/50 bg-primary/5"
              )}
            >
              <input
                id="screenplay-upload"
                type="file"
                accept=".fountain,.fdx,.txt,.md,.pdf,.docx"
                onChange={handleFileSelect}
                className="absolute inset-0 cursor-pointer opacity-0"
                aria-label="Upload screenplay file"
              />
              <div className="flex flex-col items-center gap-2 p-6 text-center">
                <Upload className="h-8 w-8 text-muted-foreground" />
                {selectedFile ? (
                  <>
                    <p className="text-sm font-medium">{selectedFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Click or drag to replace
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-medium">
                      Drop screenplay here or click to browse
                    </p>
                    <p className="text-xs text-muted-foreground">
                      PDF, Final Draft (.fdx), Fountain, Markdown, TXT, or DOCX
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Project Name — appears after file selection */}
          {selectedFile && (
            <div className="space-y-2">
              <label htmlFor="project-name" className="text-sm font-medium flex items-center gap-2">
                Project Name
                {isNaming && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Reading title...
                  </span>
                )}
                {!isNaming && nameSource === 'ai' && (
                  <span className="flex items-center gap-1 text-xs text-primary">
                    <Sparkles className="h-3 w-3" />
                    AI-detected
                  </span>
                )}
              </label>
              <Input
                id="project-name"
                placeholder="Enter project name"
                value={projectName}
                onChange={(e) => handleNameChange(e.target.value)}
                disabled={isNaming}
              />
              {slug && !isNaming && (
                <p className="text-xs text-muted-foreground">
                  URL: <code className="rounded bg-muted px-1 py-0.5">/{slug}</code>
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => navigate('/')}
              className="flex-1"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!canCreate || isProcessing}
              className="flex-1"
            >
              <Plus className="mr-2 h-4 w-4" />
              {isProcessing ? 'Creating...' : 'Create Project'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function cleanFilename(filename: string): string {
  let name = filename
    .replace(/\.(pdf|fdx|fountain|txt|md|docx)$/i, '')
    .replace(/^\d{10,15}[_-]/, '')
    .replace(/[_-]/g, ' ')
    .replace(/\s+No\s+ID\s*$/i, '')
    .replace(/\s+/g, ' ')
    .trim()
  if (name) {
    name = name
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(' ')
  }
  return name
}

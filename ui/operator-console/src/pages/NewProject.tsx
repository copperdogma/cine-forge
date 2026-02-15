import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useCreateProject } from '@/lib/hooks'
import { uploadProjectInput } from '@/lib/api'

export default function NewProject() {
  const navigate = useNavigate()
  const [projectName, setProjectName] = useState('')
  const [projectPath, setProjectPath] = useState('output/')
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const createProject = useCreateProject()

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
      // Auto-populate project name from filename if empty
      if (!projectName) {
        const nameWithoutExt = validFile.name.replace(/\.(pdf|fdx|fountain|txt|md|docx)$/i, '')
        setProjectName(nameWithoutExt)
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
      // Auto-populate project name from filename if empty
      if (!projectName) {
        const nameWithoutExt = files[0].name.replace(/\.(pdf|fdx|fountain|txt|md|docx)$/i, '')
        setProjectName(nameWithoutExt)
      }
    }
  }

  const handleCreate = async () => {
    if (!selectedFile) return

    const timestamp = Date.now()
    const sanitizedName = projectName.trim().replace(/[^a-zA-Z0-9_-]/g, '_')
    const fullPath = `${projectPath.replace(/\/$/, '')}/${timestamp}_${sanitizedName}`

    try {
      setIsUploading(true)

      // Step 1: Create the project
      const project = await createProject.mutateAsync(fullPath)

      // Step 2: Upload the input file (call API directly — hook would have stale projectId)
      await uploadProjectInput(project.project_id, selectedFile)

      // Step 3: Success — navigate to the project
      toast.success('Project created successfully')
      navigate(`/${project.project_id}`)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create project'
      toast.error(message)
    } finally {
      setIsUploading(false)
    }
  }

  const canCreate = projectName.trim() !== '' && selectedFile !== null
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
          {/* Project Name */}
          <div className="space-y-2">
            <label htmlFor="project-name" className="text-sm font-medium">
              Project Name
            </label>
            <Input
              id="project-name"
              placeholder="Enter project name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
            />
          </div>

          {/* Project Path */}
          <div className="space-y-2">
            <label htmlFor="project-path" className="text-sm font-medium">
              Project Path
            </label>
            <Input
              id="project-path"
              placeholder="/data/projects/"
              value={projectPath}
              onChange={(e) => setProjectPath(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Base directory where project artifacts will be stored
            </p>
          </div>

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

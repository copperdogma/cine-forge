import { type ReactNode } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useEditArtifact } from '@/lib/hooks'

type ArtifactReviewControlsProps = {
  projectId: string
  artifactType: string
  entityId: string
  data: Record<string, unknown>
  label: string
  editable?: boolean
  extraBadges?: ReactNode
}

export function ArtifactReviewControls({
  projectId,
  artifactType,
  entityId,
  data,
  label,
  editable = true,
  extraBadges,
}: ArtifactReviewControlsProps) {
  const editArtifact = useEditArtifact()
  const userApproved = data.user_approved === true

  async function handleApprovalToggle() {
    try {
      await editArtifact.mutateAsync({
        projectId,
        artifactType,
        entityId,
        payload: {
          data: {
            ...data,
            user_approved: !userApproved,
          },
          rationale: userApproved
            ? `Return ${label} to draft state`
            : `Mark ${label} as reviewed`,
        },
      })
      toast.success(userApproved ? 'Marked as draft' : 'Marked as reviewed')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update review state')
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant={userApproved ? 'default' : 'outline'}>
        {userApproved ? 'Reviewed' : 'Draft'}
      </Badge>
      {extraBadges}
      {editable && (
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={handleApprovalToggle}
          disabled={editArtifact.isPending}
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          {userApproved ? 'Mark Draft' : 'Mark Reviewed'}
        </Button>
      )}
    </div>
  )
}

import { Card, CardContent } from '@/components/ui/card'
import { DesignStudySection } from '@/components/DesignStudySection'
import { ReferenceLibrarySection } from '@/components/assets/ReferenceLibrarySection'
import type { DesignStudyEntityType, DesignStudyState } from '@/lib/api'

interface EntityReferenceStudioProps {
  projectId: string
  targetId: string
  entityType: DesignStudyEntityType
  designStudyEntityId: string
  designStudyState: DesignStudyState | null
}

const PURPOSE_PRESETS: Record<DesignStudyEntityType, string[]> = {
  character: ['actor_photo', 'wardrobe_reference', 'mood_board', 'makeup_reference'],
  location: ['scout_photo', 'lighting_reference', 'mood_board', 'set_detail'],
  prop: ['hero_prop', 'texture_reference', 'detail_reference', 'mood_board'],
}

const ACTIVE_HINTS: Record<DesignStudyEntityType, string> = {
  character: 'Downstream visual references include every uploaded character image plus the current AI final/favorite pick.',
  location: 'Look & Feel sees uploaded location references alongside the current AI design-study pick for this location.',
  prop: 'Prop references stay origin-agnostic: uploaded details and the current AI design-study pick travel through the same downstream imagery path.',
}

export function EntityReferenceStudio({
  projectId,
  targetId,
  entityType,
  designStudyEntityId,
  designStudyState,
}: EntityReferenceStudioProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(340px,0.9fr)]">
      <ReferenceLibrarySection
        projectId={projectId}
        targetKind={entityType}
        targetId={targetId}
        title="Reference Library"
        description="Uploaded references and AI design-study outputs browse together here. This is the operator-facing visual stack for the current entity."
        purposePresets={PURPOSE_PRESETS[entityType]}
        activeReferenceHint={ACTIVE_HINTS[entityType]}
        designStudyState={designStudyState}
        designStudyEntityId={designStudyEntityId}
      />

      <Card>
        <CardContent className="pt-5">
          <DesignStudySection
            projectId={projectId}
            entityId={designStudyEntityId}
            entityType={entityType}
          />
        </CardContent>
      </Card>
    </div>
  )
}

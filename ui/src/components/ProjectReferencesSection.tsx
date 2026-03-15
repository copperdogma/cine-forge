import { ReferenceLibrarySection } from '@/components/assets/ReferenceLibrarySection'

interface ProjectReferencesSectionProps {
  projectId: string
}

export function ProjectReferencesSection({ projectId }: ProjectReferencesSectionProps) {
  return (
    <ReferenceLibrarySection
      projectId={projectId}
      targetKind="project"
      targetId="project"
      title="Project References"
      description="Global look boards, palette stills, temp music, and supporting documents live here. These references apply across scenes unless a scene or entity carries its own more specific material."
      purposePresets={['style_reference', 'mood_board', 'temp_score', 'lookbook_pdf']}
      activeReferenceHint="Project-level references are the top of the shared stack: scene-local uploads add to them, and entity pages contribute their own design-study and uploaded visuals downstream."
    />
  )
}

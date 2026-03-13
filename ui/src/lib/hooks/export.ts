import { useEntityDetails, useScenes } from './entities'
import { useProject } from './projects'

export function useExportData(projectId: string | undefined) {
  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: scenes, isLoading: scenesLoading } = useScenes(projectId)
  const { data: characters, isLoading: charactersLoading } = useEntityDetails(projectId, 'character_bible')
  const { data: locations, isLoading: locationsLoading } = useEntityDetails(projectId, 'location_bible')
  const { data: props, isLoading: propsLoading } = useEntityDetails(projectId, 'prop_bible')

  const isLoading = (
    projectLoading
    || scenesLoading
    || charactersLoading
    || locationsLoading
    || propsLoading
  )

  return {
    data: {
      summary: project,
      scenes: scenes ?? [],
      characters: characters ?? [],
      locations: locations ?? [],
      props: props ?? [],
    },
    isLoading,
  }
}

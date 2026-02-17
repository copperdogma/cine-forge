import { create } from 'zustand'

interface AppStore {
  // Map of projectId -> display name, populated when projects are loaded
  projectNames: Record<string, string>
  setProjectName: (id: string, name: string) => void
}

export const useAppStore = create<AppStore>((set) => ({
  projectNames: {},
  setProjectName: (id, name) => set((s) => ({
    projectNames: { ...s.projectNames, [id]: name }
  })),
}))

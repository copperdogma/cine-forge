import type { SceneWorkspaceTab } from './constants'

export type SceneWorkflowGuide = {
  stepId: 'shots' | 'storyboard' | 'render' | 'done'
  stepNumber: number
  totalSteps: number
  title: string
  description: string
  hint: string
  actionLabel: string | null
  targetTab: SceneWorkspaceTab | null
  actionKind: 'route' | 'jump' | 'none'
}

export type SceneWorkflowState = {
  activeTab: SceneWorkspaceTab
  hasShotPlan: boolean
  hasStoryboard: boolean
  hasRender: boolean
}

const TOTAL_STEPS = 3

export function getSceneWorkflowGuide(state: SceneWorkflowState): SceneWorkflowGuide {
  const { activeTab, hasShotPlan, hasStoryboard, hasRender } = state

  if (hasRender) {
    if (activeTab === 'render') {
      return {
        stepId: 'done',
        stepNumber: TOTAL_STEPS,
        totalSteps: TOTAL_STEPS,
        title: 'Rendered scene ready',
        description:
          'This scene already has a full render. You can refine it here or move on to the next scene.',
        hint: 'This scene already has a full render.',
        actionLabel: null,
        targetTab: null,
        actionKind: 'none',
      }
    }

    return {
      stepId: 'done',
      stepNumber: TOTAL_STEPS,
      totalSteps: TOTAL_STEPS,
      title: 'Rendered scene ready',
      description:
        'This scene already has a full render. Open the Render tab to review the latest video, prompt, and validation artifacts.',
      hint: 'This scene already has a full render waiting in the Render tab.',
      actionLabel: 'Open Render',
      targetTab: 'render',
      actionKind: 'route',
    }
  }

  if (!hasShotPlan) {
    const onShotsTab = activeTab === 'shots'
    return {
      stepId: 'shots',
      stepNumber: 1,
      totalSteps: TOTAL_STEPS,
      title: onShotsTab ? 'Next: run shot planning for this scene' : 'Next: build the shot plan',
      description: onShotsTab
        ? 'Use the panel below to turn this scene into a cuttable shot list. Storyboards and the final render build from that structure.'
        : 'After direction work, turn this scene into a cuttable shot list. Storyboards and the final render build from that structure.',
      hint: 'Next: build the shot plan for this scene so storyboards and the final render have real structure.',
      actionLabel: onShotsTab ? 'Jump to Shot Planning' : 'Open Shots',
      targetTab: 'shots',
      actionKind: onShotsTab ? 'jump' : 'route',
    }
  }

  if (!hasStoryboard) {
    const onStoryboardTab = activeTab === 'storyboard'
    return {
      stepId: 'storyboard',
      stepNumber: 2,
      totalSteps: TOTAL_STEPS,
      title: onStoryboardTab ? 'Next: run storyboard generation' : 'Next: turn shots into storyboard frames',
      description: onStoryboardTab
        ? 'Use the panel below to turn the current shot plan into storyboard frames. Render is the step after this.'
        : 'The shot plan is ready. Turn it into storyboard frames next, then move into Render for the final scene video.',
      hint: 'Next: turn the shot plan into storyboard frames, then move into Render for the final scene video.',
      actionLabel: onStoryboardTab ? 'Jump to Storyboard' : 'Open Storyboard',
      targetTab: 'storyboard',
      actionKind: onStoryboardTab ? 'jump' : 'route',
    }
  }

  const onRenderTab = activeTab === 'render'
  return {
    stepId: 'render',
    stepNumber: 3,
    totalSteps: TOTAL_STEPS,
    title: onRenderTab ? 'Final step: run render for this scene' : 'Next: render this scene',
    description: onRenderTab
      ? 'Use the panel below to generate the provider-ready prompt and final scene video. AI Previz remains optional if you want a motion-planning pass first.'
      : 'The shot plan and storyboard are ready. Move into Render for the final scene video. AI Previz remains optional if you want a motion-planning pass first.',
    hint: 'Next: move into Render for the final scene video.',
    actionLabel: onRenderTab ? 'Jump to Render' : 'Open Render',
    targetTab: 'render',
    actionKind: onRenderTab ? 'jump' : 'route',
  }
}

import type { ProjectSummary } from "@/lib/types"

export const NO_SAVED_MODEL_OVERRIDE = "__unset__"
export const PROJECT_DEFAULT_MODEL = "claude-sonnet-4-6"
export const PROJECT_RUN_WORK_MODEL = "claude-haiku-4-5-20251001"

export type ProjectModelFormState = {
  defaultModel: string
  workModel: string
  verifyModel: string
  escalateModel: string
}

type ProjectModelSummary = Pick<
  ProjectSummary,
  "default_model" | "work_model" | "verify_model" | "escalate_model"
>

export const PROJECT_MODEL_OPTIONS = [
  { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5" },
  { value: "claude-sonnet-4-6", label: "Claude Sonnet 4.6" },
  { value: "claude-opus-4-6", label: "Claude Opus 4.6" },
  { value: "gpt-4.1-mini", label: "GPT-4.1 Mini" },
  { value: "gpt-4.1", label: "GPT-4.1" },
  { value: "gpt-5.2", label: "GPT-5.2" },
  { value: "gpt-5.4", label: "GPT-5.4" },
  { value: "gemini-2.5-flash-lite", label: "Gemini 2.5 Flash Lite" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { value: "gemini-3-flash-preview", label: "Gemini 3 Flash" },
  { value: "gemini-3.1-flash-lite-preview", label: "Gemini 3.1 Flash Lite" },
  { value: "gemini-3.1-pro-preview", label: "Gemini 3.1 Pro" },
]

export const OPTIONAL_PROJECT_MODEL_OPTIONS = [
  { value: NO_SAVED_MODEL_OVERRIDE, label: "No saved override" },
  ...PROJECT_MODEL_OPTIONS,
]

export function getPersistedProjectModelState(project?: ProjectModelSummary) {
  return {
    default_model: project?.default_model ?? null,
    work_model: project?.work_model ?? null,
    verify_model: project?.verify_model ?? null,
    escalate_model: project?.escalate_model ?? null,
  }
}

export function getProjectModelFormState(project?: ProjectModelSummary): ProjectModelFormState {
  return {
    defaultModel: project?.default_model ?? PROJECT_DEFAULT_MODEL,
    workModel: project?.work_model ?? NO_SAVED_MODEL_OVERRIDE,
    verifyModel: project?.verify_model ?? NO_SAVED_MODEL_OVERRIDE,
    escalateModel: project?.escalate_model ?? NO_SAVED_MODEL_OVERRIDE,
  }
}

export function normalizeProjectModelSettings(state: ProjectModelFormState) {
  return {
    default_model: state.defaultModel,
    work_model: state.workModel === NO_SAVED_MODEL_OVERRIDE ? null : state.workModel,
    verify_model: state.verifyModel === NO_SAVED_MODEL_OVERRIDE ? null : state.verifyModel,
    escalate_model: state.escalateModel === NO_SAVED_MODEL_OVERRIDE ? null : state.escalateModel,
  }
}

export function getProjectRunModelDefaults(project?: ProjectModelSummary) {
  return {
    defaultModel: project?.default_model ?? PROJECT_DEFAULT_MODEL,
    workModel: project?.work_model ?? PROJECT_RUN_WORK_MODEL,
    verifyModel: project?.verify_model ?? "",
  }
}

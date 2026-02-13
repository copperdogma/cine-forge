export type ApiError = {
  code: string;
  message: string;
  hint?: string | null;
};

export type ProjectSummary = {
  project_id: string;
  display_name: string;
  artifact_groups: number;
  run_count: number;
};

export type RecentProjectSummary = ProjectSummary & {
  project_path: string;
};

export type RunSummary = {
  run_id: string;
  status: string;
  started_at?: number;
  finished_at?: number;
};

export type UploadedInputResponse = {
  original_name: string;
  stored_path: string;
  size_bytes: number;
};

export type ArtifactGroupSummary = {
  artifact_type: string;
  entity_id: string | null;
  latest_version: number;
  health: string | null;
};

export type ArtifactVersionSummary = {
  artifact_type: string;
  entity_id: string | null;
  version: number;
  health: string | null;
  path: string;
  created_at?: string;
  intent?: string;
  producing_module?: string;
};

export type RunStateResponse = {
  run_id: string;
  state: {
    run_id: string;
    recipe_id: string;
    started_at?: number;
    finished_at?: number;
    stages: Record<
      string,
      {
        status: string;
        duration_seconds: number;
        cost_usd: number;
        artifact_refs: Array<Record<string, unknown>>;
      }
    >;
    total_cost_usd: number;
  };
  background_error?: string | null;
};

export type RunEventsResponse = {
  run_id: string;
  events: Array<Record<string, unknown>>;
};

export type ArtifactDetailResponse = {
  artifact_type: string;
  entity_id: string | null;
  version: number;
  payload: Record<string, unknown>;
};

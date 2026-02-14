import { createContext, useContext, useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { Navigate, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  createProject,
  getArtifact,
  getProject,
  getRunEvents,
  getRunState,
  listArtifactGroups,
  listArtifactVersions,
  listRecentProjects,
  listRuns,
  openProject,
  startRun,
  uploadProjectInput,
} from "./api";
import type {
  ArtifactDetailResponse,
  ArtifactGroupSummary,
  ArtifactVersionSummary,
  ProjectSummary,
  RecentProjectSummary,
  RunEventsResponse,
  RunStateResponse,
  RunSummary,
} from "./types";

type SessionProject = {
  id: string;
  label: string;
  path: string;
};

const ProjectContext = createContext<SessionProject | null>(null);

function useProject() {
  return useContext(ProjectContext);
}

const DEFAULT_INPUT = "tests/fixtures/sample_screenplay.fountain";

function useAsyncError() {
  const [error, setError] = useState<string>("");
  return {
    error,
    clear: () => setError(""),
    from: (value: unknown) => {
      if (value instanceof Error) {
        setError(value.message);
        return;
      }
      setError(String(value));
    },
  };
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48);
}

function filenameStem(pathValue: string): string {
  const clean = pathValue.trim().split(/[\\/]/).filter(Boolean).pop() ?? "project";
  const withoutExt = clean.replace(/\.[^.]+$/, "");
  return withoutExt || "project";
}

function formatDuration(seconds: number): string {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  }
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function formatModel(model: string | null | undefined, callCount: number | undefined): { label: string; title?: string } {
  // If callCount is 0, it means no AI was actually called (deterministic pass)
  if (!model || model === "code" || model === "none" || callCount === 0) {
    return { label: "code" };
  }
  
  const calls = callCount && callCount > 1 ? ` (${callCount} calls)` : "";
  
  if (model.startsWith("mixed:")) {
    const models = model.substring(6); // remove "mixed:"
    return { 
      label: `Code + ${models.split("+")[0]}${calls}`, 
      title: `Hybrid: Code and ${models.replace(/\+/g, ", ")}`
    };
  }
  
  if (model.includes("+")) {
    const list = model.split("+");
    return {
      label: `${list[0]}${calls}`,
      title: `Multiple models: ${list.join(", ")}`
    };
  }

  return { label: `${model}${calls}` };
}

function StatusBadge({ status }: { status: string }) {
  let className = "badge";
  if (status === "done" || status === "skipped_reused") {
    className += " badge-success";
  } else if (status === "failed") {
    className += " badge-error";
  } else if (status === "running") {
    className += " badge-info badge-pulse";
  } else {
    className += " badge-muted";
  }
  return <span className={className}>{status}</span>;
}

export function App() {
  const [seedInputPath, setSeedInputPath] = useState(DEFAULT_INPUT);
  const [recentProjects, setRecentProjects] = useState<RecentProjectSummary[]>([]);
  const [projectsError, setProjectsError] = useState("");
  const [switcherOpen, setSwitcherOpen] = useState(false);

  async function refreshProjects() {
    setProjectsError("");
    try {
      const projects = await listRecentProjects();
      setRecentProjects(projects);
    } catch (error) {
      setProjectsError(error instanceof Error ? error.message : String(error));
    }
  }

  useEffect(() => {
    void refreshProjects();
  }, []);

  return (
    <div className="container">
      <Routes>
        <Route
          path="/"
          element={
            <LandingPage
              projects={recentProjects}
              error={projectsError}
              refresh={refreshProjects}
              setSeedInputPath={setSeedInputPath}
            />
          }
        />
        <Route
          path="/new"
          element={
            <div className="page-wrapper">
              <Header label="(new project)" onOpenSwitcher={() => setSwitcherOpen(true)} />
              <NewProjectPage
                onProjectCreated={(_, inputPath) => {
                  setSeedInputPath(inputPath);
                  setSwitcherOpen(false);
                }}
                refreshProjects={refreshProjects}
              />
            </div>
          }
        />
        <Route
          path="/:projectId/*"
          element={
            <ProjectLayout
              recentProjects={recentProjects}
              seedInputPath={seedInputPath}
              setSwitcherOpen={setSwitcherOpen}
            />
          }
        />
      </Routes>

      {switcherOpen ? (
        <ProjectSwitcher
          activeProject={null}
          projects={recentProjects}
          projectsError={projectsError}
          canClose={true}
          modal={true}
          onClose={() => setSwitcherOpen(false)}
          onActivate={(_, inputPath) => {
            if (inputPath) {
              setSeedInputPath(inputPath);
            }
            setSwitcherOpen(false);
          }}
          onRefresh={() => void refreshProjects()}
        />
      ) : null}
    </div>
  );
}

function Header({ label, onOpenSwitcher }: { label: string; onOpenSwitcher: () => void }) {
  return (
    <header className="topbar">
      <div>
        <h1>CineForge Operator Console Lite</h1>
        <p>
          Active project: <strong>{label}</strong>
        </p>
      </div>
      <button className="secondary projects-toggle" onClick={onOpenSwitcher}>
        Projects
      </button>
    </header>
  );
}

function LandingPage({
  projects,
  error,
  refresh,
  setSeedInputPath,
}: {
  projects: RecentProjectSummary[];
  error: string;
  refresh: () => void;
  setSeedInputPath: (path: string) => void;
}) {
  const navigate = useNavigate();
  return (
    <div className="page-wrapper">
      <Header label="(select project)" onOpenSwitcher={() => {}} />
      <ProjectSwitcher
        activeProject={null}
        projects={projects}
        projectsError={error}
        canClose={false}
        modal={false}
        onClose={() => {}}
        onActivate={(next, inputPath) => {
          if (inputPath) setSeedInputPath(inputPath);
          navigate(`/${next.id}/run`);
        }}
        onRefresh={refresh}
      />
      <div style={{ textAlign: "center", marginTop: "20px" }}>
        <button className="secondary" onClick={() => navigate("/new")}>
          Create Brand New Project
        </button>
      </div>
    </div>
  );
}

function Breadcrumbs({ project, page }: { project: { label: string; id: string } | null; page: string }) {
  return (
    <div className="small muted" style={{ marginBottom: "12px" }}>
      <NavLink to="/" style={{ color: "inherit", textDecoration: "none" }}>
        Projects
      </NavLink>
      {" > "}
      {project ? (
        <NavLink to={`/${project.id}/run`} style={{ color: "inherit", textDecoration: "none" }}>
          {project.label}
        </NavLink>
      ) : (
        "..."
      )}
      {" > "}
      <strong>{page}</strong>
    </div>
  );
}

function ProjectLayout({
  recentProjects,
  seedInputPath,
  setSwitcherOpen,
}: {
  recentProjects: RecentProjectSummary[];
  seedInputPath: string;
  setSwitcherOpen: (o: boolean) => void;
}) {
  const { projectId } = useParams();
  const [fetchedProject, setFetchedProject] = useState<SessionProject | null>(null);

  const project = useMemo(() => {
    const p = recentProjects.find((p) => p.project_id === projectId);
    if (p) return { id: p.project_id, label: p.display_name, path: p.project_path };
    return fetchedProject;
  }, [recentProjects, projectId, fetchedProject]);

  useEffect(() => {
    if (projectId && !recentProjects.find((p) => p.project_id === projectId)) {
      getProject(projectId)
        .then((p: ProjectSummary) => {
          setFetchedProject({ id: p.project_id, label: p.display_name, path: "" });
        })
        .catch(() => {
          // ignore project fetch error in layout, sub-pages will handle missing project
        });
    }
  }, [projectId, recentProjects]);

  // Determine current page label for breadcrumbs
  const location = window.location.pathname;
  let pageLabel = "Dashboard";
  if (location.endsWith("/run")) pageLabel = "Run Pipeline";
  if (location.endsWith("/runs")) pageLabel = "Runs / Events";
  if (location.endsWith("/artifacts")) pageLabel = "Artifacts Browser";

  return (
    <ProjectContext.Provider value={project || { id: projectId!, label: projectId!, path: "" }}>
      <div className="project-wrapper">
        <Header label={project?.label || projectId || ""} onOpenSwitcher={() => setSwitcherOpen(true)} />

        <Breadcrumbs project={project || { id: projectId!, label: projectId! }} page={pageLabel} />

        <nav className="nav">
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to={`/${projectId}/run`}>
            Run Pipeline
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to={`/${projectId}/runs`}>
            Runs / Events
          </NavLink>
          <NavLink
            className={({ isActive }) => (isActive ? "active" : "")}
            to={`/${projectId}/artifacts`}
          >
            Artifacts
          </NavLink>
        </nav>

        <Routes>
          <Route path="/" element={<Navigate to="run" replace />} />
          <Route path="run" element={<RunPage seedInputPath={seedInputPath} />} />
          <Route path="run/:runId" element={<RunPage seedInputPath={seedInputPath} />} />
          <Route path="runs" element={<RunsPage />} />
          <Route path="runs/:runId" element={<RunsPage />} />
          <Route path="artifacts" element={<ArtifactsPage />} />
          <Route path="artifacts/:artifactType/:entityId/:version" element={<ArtifactsPage />} />
        </Routes>
      </div>
    </ProjectContext.Provider>
  );
}

function ProjectSwitcher({
  activeProject,
  projects,
  projectsError,
  canClose,
  modal,
  onClose,
  onActivate,
  onRefresh,
}: {
  activeProject: SessionProject | null;
  projects: RecentProjectSummary[];
  projectsError: string;
  canClose: boolean;
  modal: boolean;
  onClose: () => void;
  onActivate: (project: SessionProject, inputPath?: string) => void;
  onRefresh: () => void;
}) {
  const navigate = useNavigate();
  const [manualPath, setManualPath] = useState("");
  const status = useAsyncError();

  async function activateFromPath(projectPath: string) {
    status.clear();
    try {
      const result = await openProject(projectPath);
      onActivate({ id: result.project_id, label: result.display_name, path: projectPath });
      navigate(`/${result.project_id}/run`);
      onRefresh();
    } catch (error) {
      status.from(error);
    }
  }

  const drawer = (
    <section className="project-drawer card">
        <div className="drawer-header">
          <h2>Projects</h2>
          <div className="drawer-actions">
            <button className="secondary compact" onClick={onRefresh}>
              Refresh
            </button>
            {canClose ? (
              <button className="ghost compact" onClick={onClose}>
                Close
              </button>
            ) : null}
          </div>
        </div>

        {projectsError ? <p className="status-error small">{projectsError}</p> : null}

        <div className="project-list">
          {projects.map((item) => {
            const active = activeProject?.id === item.project_id;
            return (
              <button
                key={item.project_id}
                className={`project-item ${active ? "active" : ""}`}
                onClick={() => void activateFromPath(item.project_path)}
              >
                <span className="project-name">{item.display_name}</span>
                <span className="project-meta">{item.run_count} runs</span>
              </button>
            );
          })}
        </div>

        {!projects.length ? (
          <p className="small">No projects yet. Create one from a script file in New Project.</p>
        ) : null}

        <div className="drawer-footer">
          <label htmlFor="manual-path">Add Existing Project Path</label>
          <input
            id="manual-path"
            value={manualPath}
            placeholder="/path/to/project"
            onChange={(event) => setManualPath(event.target.value)}
          />
          <button
            className="secondary"
            disabled={!manualPath.trim()}
            onClick={() => void activateFromPath(manualPath.trim())}
          >
            Add Project
          </button>
        </div>

        {status.error ? <p className="status-error small">{status.error}</p> : null}
      </section>
  );

  if (!modal) {
    return <div className="project-inline">{drawer}</div>;
  }

  return <div className="project-overlay">{drawer}</div>;
}

function NewProjectPage({
  onProjectCreated,
  refreshProjects,
}: {
  onProjectCreated: (project: SessionProject, inputPath: string) => void;
  refreshProjects: () => Promise<void>;
}) {
  const navigate = useNavigate();
  const [projectName, setProjectName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const status = useAsyncError();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const displayFileName = selectedFile?.name ?? "No file selected";

  const derivedProjectName = useMemo(() => {
    const base = projectName.trim() || filenameStem(selectedFile?.name ?? "project");
    const slug = slugify(base);
    return slug || "project_operator_console";
  }, [projectName, selectedFile]);

  const derivedProjectPath = useMemo(() => `output/${derivedProjectName}`, [derivedProjectName]);

  async function onCreate() {
    if (!selectedFile) {
      status.from(new Error("Choose a script/story file first."));
      return;
    }

    status.clear();
    try {
      const project = await createProject(derivedProjectPath);
      const upload = await uploadProjectInput(project.project_id, selectedFile);
      const nextProject = {
        id: project.project_id,
        label: project.display_name,
        path: derivedProjectPath,
      };
      onProjectCreated(nextProject, upload.stored_path);
      await refreshProjects();
      navigate(`/${project.project_id}/run`);
    } catch (error) {
      status.from(error);
    }
  }

  function onDropFile(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  }

  return (
    <section className="card">
      <h2>Start a New Project</h2>
      <p className="small">
        Choose a story/script file. CineForge creates the project workspace and wires the run input.
      </p>

      <div
        className={`dropzone ${dragOver ? "dragover" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDropFile}
      >
        <p>
          <strong>Drag and drop your script here</strong>
        </p>
        <p className="small muted">or</p>
        <button
          type="button"
          className="secondary file-picker-btn"
          onClick={() => fileInputRef.current?.click()}
        >
          Choose File
        </button>
        <input
          ref={fileInputRef}
          className="hidden-input"
          type="file"
          accept=".fountain,.fdx,.txt,.md,.pdf,.docx"
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            setSelectedFile(file);
          }}
        />
      </div>

      <p className="small">
        Selected file: <strong>{displayFileName}</strong>
      </p>

      <label htmlFor="project-name">Project Name (optional)</label>
      <input
        id="project-name"
        value={projectName}
        placeholder="Leave blank to derive from script filename"
        onChange={(event) => setProjectName(event.target.value)}
      />

      <details className="small" style={{ marginTop: "8px" }}>
        <summary>Storage details</summary>
        <p className="muted">
          Workspace folder: <code>{derivedProjectPath}</code>
        </p>
        <p className="muted">Input copy is stored under that project's `inputs/` directory.</p>
      </details>

      <button disabled={!selectedFile} onClick={() => void onCreate()}>
        Create Project From File
      </button>

      {status.error ? <p className="status-error">{status.error}</p> : null}
    </section>
  );
}

type ModelProfile = "mock" | "draft" | "production";

function RunPage({ seedInputPath }: { seedInputPath: string }) {
  const project = useProject();
  const { runId = "" } = useParams();
  const navigate = useNavigate();

  const setRunId = (id: string) => {
    if (id) {
      navigate(`/${project?.id}/run/${id}`, { replace: true });
    } else {
      navigate(`/${project?.id}/run`, { replace: true });
    }
  };

  const [inputFile, setInputFile] = useState(seedInputPath || DEFAULT_INPUT);
  const [profile, setProfile] = useState<ModelProfile>("mock");
  const [expertMode, setExpertMode] = useState(false);
  const [workModel, setWorkModel] = useState("gpt-4o-mini");
  const [verifyModel, setVerifyModel] = useState("gpt-4o-mini");
  const [escalateModel, setEscalateModel] = useState("gpt-4o");
  
  const [recipeId, setRecipeId] = useState("mvp_ingest");
  const [runMode, setRunMode] = useState<"accept" | "review">("accept");
  const [runState, setRunState] = useState<RunStateResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [draftDetail, setDraftDetail] = useState<ArtifactDetailResponse | null>(null);
  const [draftEdit, setDraftEdit] = useState<Record<string, unknown> | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const status = useAsyncError();

  useEffect(() => {
    setInputFile(seedInputPath || DEFAULT_INPUT);
  }, [seedInputPath]);

  // Initial fetch on mount if runId exists
  useEffect(() => {
    if (runId && !runState) {
      void getRunState(runId).then(setRunState).catch(() => {});
    }
  }, [runId]);

  useEffect(() => {
    if (!runId) {
      setIsPolling(false);
      return;
    }
    setIsPolling(true);
    const timer = window.setInterval(() => {
      void getRunState(runId)
        .then((result) => {
          setRunState(result);
          // Stop polling if run is finished or failed
          const stageValues = Object.values(result.state.stages);
          const statuses = stageValues.map((s) => s.status);
          const hasFailed = statuses.includes("failed") || result.background_error;
          const isAllDone =
            stageValues.length > 0 &&
            statuses.every((s) => ["done", "skipped_reused", "paused"].includes(s));
          const hasFinished = result.state.finished_at != null;
          if (hasFailed || isAllDone || hasFinished) {
            window.clearInterval(timer);
            setIsPolling(false);
          }
        })
        .catch((err) => {
          console.warn("[CineForge] polling error:", err);
        });
    }, 1000);
    return () => {
      window.clearInterval(timer);
      setIsPolling(false);
    };
  }, [runId]);

  const stageRows = useMemo(() => {
    if (!runState) {
      return [];
    }
    return Object.entries(runState.state.stages).sort((a, b) => {
      const aStart = a[1].started_at || Number.MAX_SAFE_INTEGER;
      const bStart = b[1].started_at || Number.MAX_SAFE_INTEGER;
      if (aStart !== bStart) {
        return aStart - bStart;
      }
      return a[0].localeCompare(b[0]);
    });
  }, [runState]);

  async function start(acceptConfig: boolean, configOverrides?: Record<string, unknown>, startFrom?: string) {
    if (!project) {
      status.from(new Error("Choose or create a project first."));
      return;
    }
    status.clear();
    setDraftDetail(null);
    setDraftEdit(null);

    const sota = "gpt-4o";
    const utility = "gpt-4o-mini";

    let work = expertMode ? workModel : "mock";
    let verify = expertMode ? verifyModel : "mock";
    let escalate = expertMode ? escalateModel : "mock";

    if (!expertMode) {
      if (profile === "draft") {
        work = utility;
        verify = utility;
        escalate = sota;
      } else if (profile === "production") {
        work = utility;
        verify = sota;
        escalate = sota;
      }
    }

    try {
      const started = await startRun({
        project_id: project.id,
        input_file: inputFile,
        default_model: work, // backward compat
        work_model: work,
        verify_model: verify,
        escalate_model: escalate,
        recipe_id: recipeId,
        accept_config: acceptConfig,
        skip_qa: profile === "mock",
        force: true,
        config_overrides: configOverrides,
        start_from: startFrom,
      });
      setRunId(started.run_id);
      await waitForInitialRunState(started.run_id);
      if (!acceptConfig) {
        setDraftLoading(true);
        await waitForDraft(project.id, started.run_id);
        setDraftLoading(false);
      }
    } catch (error) {
      setDraftLoading(false);
      status.from(error);
    }
  }

  async function waitForInitialRunState(activeRunId: string): Promise<void> {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      try {
        const current = await getRunState(activeRunId);
        setRunState(current);
        return;
      } catch {
        await new Promise((resolve) => window.setTimeout(resolve, 500));
      }
    }
    throw new Error(`Run state not found for run_id='${activeRunId}'.`);
  }

  async function loadLatestDraft(projectId: string): Promise<boolean> {
    const groups = await listArtifactGroups(projectId);
    const draftGroup = groups.find((group) => group.artifact_type === "draft_project_config");
    if (!draftGroup) {
      return false;
    }
    const entityId = draftGroup.entity_id ?? "__project__";
    const versions = await listArtifactVersions(projectId, "draft_project_config", entityId);
    if (!versions.length) {
      return false;
    }
    const latest = versions[versions.length - 1];
    const detail = await getArtifact(projectId, "draft_project_config", entityId, latest.version);
    setDraftDetail(detail);
    const payload = detail.payload as { data?: Record<string, unknown> };
    setDraftEdit(payload.data ? { ...payload.data } : null);
    return true;
  }

  async function waitForDraft(projectId: string, activeRunId: string): Promise<void> {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      const loaded = await loadLatestDraft(projectId);
      if (loaded) {
        return;
      }
      const current = await getRunState(activeRunId);
      setRunState(current);
      const projectConfigStage = current.state.stages.project_config;
      if (
        projectConfigStage &&
        ["paused", "done", "failed", "skipped_reused"].includes(projectConfigStage.status)
      ) {
        await loadLatestDraft(projectId);
        return;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 500));
    }
  }

  function updateDraftField(key: string, value: string) {
    setDraftEdit((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        [key]: value,
      };
    });
  }

  function updateModelStrategyField(key: string, value: string) {
    setDraftEdit((current) => {
      if (!current) {
        return current;
      }
      const strategy = (current.model_strategy as Record<string, string>) || {
        work: "gpt-4o-mini",
        verify: "gpt-4o-mini",
        escalate: "gpt-4o",
      };
      return {
        ...current,
        model_strategy: {
          ...strategy,
          [key]: value,
        },
      };
    });
  }

  const modelStrategy = (draftEdit?.model_strategy as Record<string, string>) || {};

  return (
    <section className="card">
      <h2>Run Pipeline</h2>
      {!project ? <p className="status-error">Choose or create a project first.</p> : null}
      <div className="grid">
        <div>
          <label htmlFor="input-file">Input File</label>
          <input
            id="input-file"
            value={inputFile}
            onChange={(event) => setInputFile(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="model-profile">Model Profile</label>
          <select
            id="model-profile"
            value={profile}
            disabled={expertMode}
            onChange={(event) => setProfile(event.target.value as ModelProfile)}
          >
            <option value="mock">Mock (Fast/Free)</option>
            <option value="draft">Drafting (Cheap/Mini)</option>
            <option value="production">Production (SOTA)</option>
          </select>
          <div style={{ marginTop: "4px" }}>
            <label className="small">
              <input
                type="checkbox"
                checked={expertMode}
                onChange={(e) => setExpertMode(e.target.checked)}
              />{" "}
              Expert Mode (Manual Overrides)
            </label>
          </div>
        </div>
        <div>
          <label htmlFor="run-mode">Config Confirmation Mode</label>
          <select
            id="run-mode"
            value={runMode}
            onChange={(event) => setRunMode(event.target.value as "accept" | "review")}
          >
            <option value="accept">Accept directly</option>
            <option value="review">Draft then review/edit</option>
          </select>
        </div>
        <div>
          <label htmlFor="recipe-id">Pipeline Recipe</label>
          <select
            id="recipe-id"
            value={recipeId}
            onChange={(event) => setRecipeId(event.target.value)}
          >
            <option value="mvp_ingest">MVP Ingest (Basic)</option>
            <option value="world_building">World Building (Bibles)</option>
          </select>
        </div>
      </div>

      {expertMode ? (
        <div
          className="grid"
          style={{
            marginTop: "10px",
            padding: "10px",
            background: "#f9f9f9",
            border: "1px solid #ddd",
            borderRadius: "4px",
          }}
        >
          <div>
            <label htmlFor="work-model">Work Model</label>
            <input id="work-model" value={workModel} onChange={(e) => setWorkModel(e.target.value)} />
          </div>
          <div>
            <label htmlFor="verify-model">Verify Model</label>
            <input
              id="verify-model"
              value={verifyModel}
              onChange={(e) => setVerifyModel(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="escalate-model">Escalate Model</label>
            <input
              id="escalate-model"
              value={escalateModel}
              onChange={(e) => setEscalateModel(e.target.value)}
            />
          </div>
        </div>
      ) : null}
      <div className="row" style={{ marginTop: "10px" }}>
        <button disabled={!project} onClick={() => void start(runMode === "accept")}>
          Start Run
        </button>
      </div>

      {status.error ? <p className="status-error">{status.error}</p> : null}
      {runId ? <p className="status-ok">Active run: {runId}</p> : null}
      {runMode === "review" && draftLoading ? (
        <p>Waiting for draft project config artifact to be generated...</p>
      ) : null}

      {runState ? (
        <div className="card">
          <h3>Stage Progress</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Stage</th>
                <th>Status</th>
                <th>Model</th>
                <th>Duration</th>
                <th>Cost (USD)</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {stageRows.map(([stageId, stage]) => (
                <tr key={stageId}>
                  <td>
                    <strong>{stageId}</strong>
                  </td>
                  <td>
                    <StatusBadge status={stage.status} />
                  </td>
                  <td>
                    {(() => {
                      const { label, title } = formatModel(stage.model_used, stage.call_count);
                      return (
                        <code style={{ fontSize: "0.9em" }} title={title}>
                          {label}
                        </code>
                      );
                    })()}
                  </td>
                  <td>{formatDuration(stage.duration_seconds)}</td>
                  <td>{stage.cost_usd > 0 ? `$${stage.cost_usd.toFixed(4)}` : "—"}</td>
                  <td>
                    <button
                      className="ghost compact"
                      disabled={isPolling || stage.status === "running"}
                      title="Re-run this stage and all downstream dependencies"
                      onClick={() => void start(true, undefined, stageId)}
                    >
                      ↺ Re-run
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <RunOutcomeSummary runState={runState} isPolling={isPolling} />
          {runState.background_error ? (
            <p className="status-error">Background error: {runState.background_error}</p>
          ) : null}
        </div>
      ) : null}

      {runMode === "review" && draftEdit ? (
        <div className="card">
          <h3>Draft Project Config Review</h3>
          <p>Adjust key fields and confirm. This writes overrides to config_file and reruns project config.</p>
          <div className="grid">
            <div>
              <label htmlFor="draft-title">Title</label>
              <input
                id="draft-title"
                value={String(draftEdit.title ?? "")}
                onChange={(event) => updateDraftField("title", event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="draft-format">Format</label>
              <input
                id="draft-format"
                value={String(draftEdit.format ?? "")}
                onChange={(event) => updateDraftField("format", event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="draft-tone">Tone (comma-separated)</label>
              <input
                id="draft-tone"
                value={Array.isArray(draftEdit.tone) ? draftEdit.tone.join(", ") : String(draftEdit.tone ?? "")}
                onChange={(event) =>
                  updateDraftField(
                    "tone",
                    event.target.value
                      .split(",")
                      .map((item) => item.trim())
                      .filter(Boolean)
                      .join(", "),
                  )
                }
              />
            </div>
            <div>
              <label htmlFor="draft-genre">Genre (comma-separated)</label>
              <input
                id="draft-genre"
                value={
                  Array.isArray(draftEdit.genre) ? draftEdit.genre.join(", ") : String(draftEdit.genre ?? "")
                }
                onChange={(event) =>
                  updateDraftField(
                    "genre",
                    event.target.value
                      .split(",")
                      .map((item) => item.trim())
                      .filter(Boolean)
                      .join(", "),
                  )
                }
              />
            </div>
            <div>
              <label htmlFor="strategy-work">Global Work Model</label>
              <input
                id="strategy-work"
                value={modelStrategy.work ?? ""}
                onChange={(e) => updateModelStrategyField("work", e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="strategy-verify">Global Verify Model</label>
              <input
                id="strategy-verify"
                value={modelStrategy.verify ?? ""}
                onChange={(e) => updateModelStrategyField("verify", e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="strategy-escalate">Global Escalate Model</label>
              <input
                id="strategy-escalate"
                value={modelStrategy.escalate ?? ""}
                onChange={(e) => updateModelStrategyField("escalate", e.target.value)}
              />
            </div>
          </div>
          <button
            style={{ marginTop: "8px" }}
            onClick={() => {
              const overrides: Record<string, unknown> = { ...draftEdit };
              if (typeof overrides.tone === "string") {
                overrides.tone = String(overrides.tone)
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean);
              }
              if (typeof overrides.genre === "string") {
                overrides.genre = String(overrides.genre)
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean);
              }
              void start(true, overrides);
            }}
          >
            Confirm With Edits
          </button>
          {draftDetail ? (
            <details style={{ marginTop: "8px" }}>
              <summary>Raw Draft JSON</summary>
              <pre className="code">{JSON.stringify(draftDetail.payload, null, 2)}</pre>
            </details>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function RunsPage() {
  const project = useProject();
  const { runId: selectedRunId = "" } = useParams();
  const navigate = useNavigate();

  const setSelectedRunId = (id: string) => {
    navigate(`/${project?.id}/runs/${id}`);
  };

  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [state, setState] = useState<RunStateResponse | null>(null);
  const [events, setEvents] = useState<RunEventsResponse | null>(null);
  const status = useAsyncError();

  async function refreshRuns() {
    if (!project) {
      return;
    }
    status.clear();
    try {
      const list = await listRuns(project.id);
      setRuns(list);
      if (!selectedRunId && list.length) {
        setSelectedRunId(list[0].run_id);
      }
    } catch (error) {
      status.from(error);
    }
  }

  useEffect(() => {
    void refreshRuns();
  }, [project?.id]);

  async function loadRunData() {
    if (!selectedRunId) {
      setState(null);
      setEvents(null);
      return;
    }
    status.clear();
    try {
      const [nextState, nextEvents] = await Promise.all([
        getRunState(selectedRunId),
        getRunEvents(selectedRunId),
      ]);
      setState(nextState);
      setEvents(nextEvents);
    } catch (error) {
      status.from(error);
    }
  }

  useEffect(() => {
    void loadRunData();
  }, [selectedRunId]);

  return (
    <section className="card">
      <h2>Runs / Events</h2>
      {!project ? <p className="status-error">Choose or create a project first.</p> : null}
      <div className="row">
        <button className="secondary" disabled={!project} onClick={() => void refreshRuns()}>
          Refresh Runs
        </button>
        <button disabled={!project || !selectedRunId} onClick={() => void loadRunData()}>
          Load Selected Run
        </button>
      </div>
      {runs.length ? (
        <div style={{ marginTop: "8px" }}>
          <label htmlFor="run-id">Run ID</label>
          <select id="run-id" value={selectedRunId} onChange={(event) => setSelectedRunId(event.target.value)}>
            {runs.map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id} ({run.status})
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {status.error ? <p className="status-error">{status.error}</p> : null}
      {state ? (
        <div className="card">
          <h3>Run State</h3>
          <RunOutcomeSummary runState={state} isPolling={false} />
          <pre className="code">{JSON.stringify(state.state, null, 2)}</pre>
        </div>
      ) : null}
      {events ? (
        <div className="card">
          <h3>Events</h3>
          <pre className="code">{JSON.stringify(events.events, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

function ArtifactsPage() {
  const project = useProject();
  const { artifactType: selType = "", entityId: selEntity = "", version: selVersionStr = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const selFile = searchParams.get("file") || "";
  const navigate = useNavigate();

  const [groups, setGroups] = useState<ArtifactGroupSummary[]>([]);
  const [versions, setVersions] = useState<ArtifactVersionSummary[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<ArtifactDetailResponse | null>(null);
  const status = useAsyncError();

  const selectedGroup = useMemo(() => {
    return groups.find((g) => g.artifact_type === selType && (g.entity_id ?? "__project__") === selEntity) || null;
  }, [groups, selType, selEntity]);

  const selectedVersion = selVersionStr ? parseInt(selVersionStr, 10) : null;

  async function loadGroups() {
    if (!project) {
      return;
    }
    status.clear();
    try {
      const next = await listArtifactGroups(project.id);
      setGroups(next);
      if (next.length && !selType) {
        navigate(`/${project.id}/artifacts/${next[0].artifact_type}/${next[0].entity_id ?? "__project__"}/latest`, { replace: true });
      }
    } catch (error) {
      status.from(error);
    }
  }

  useEffect(() => {
    void loadGroups();
  }, [project?.id]);

  useEffect(() => {
    if (!project || !selectedGroup) {
      setVersions([]);
      return;
    }
    const entityId = selectedGroup.entity_id ?? "__project__";
    void listArtifactVersions(project.id, selectedGroup.artifact_type, entityId)
      .then((next) => {
        setVersions(next);
        if (!next.length) {
          setSelectedDetail(null);
          return;
        }
        if (!selectedVersion && selVersionStr === "latest") {
          const latest = next[next.length - 1];
          navigate(`/${project.id}/artifacts/${selectedGroup.artifact_type}/${entityId}/${latest.version}`, { replace: true });
        }
      })
      .catch((error: unknown) => status.from(error));
  }, [project?.id, selectedGroup, selVersionStr]);

  useEffect(() => {
    if (!project || !selectedGroup || !selectedVersion) {
      setSelectedDetail(null);
      return;
    }
    const entityId = selectedGroup.entity_id ?? "__project__";
    void getArtifact(project.id, selectedGroup.artifact_type, entityId, selectedVersion)
      .then((detail) => {
        setSelectedDetail(detail);
        
        // Auto-select master_definition if no file is selected and it's a bible
        if (detail.artifact_type === "bible_manifest" && !selFile) {
          const manifest = detail.payload.data as { files?: Array<{ filename: string; purpose: string }> };
          const masterFile = manifest.files?.find(f => f.purpose === "master_definition");
          if (masterFile) {
            setSearchParams((prev) => {
              prev.set("file", masterFile.filename);
              return prev;
            }, { replace: true });
          }
        }
      })
      .catch((error: unknown) => status.from(error));
  }, [project?.id, selectedGroup, selectedVersion]);

  function selectGroup(group: ArtifactGroupSummary) {
    navigate(`/${project?.id}/artifacts/${group.artifact_type}/${group.entity_id ?? "__project__"}/latest`);
  }

  function selectVersion(v: number) {
    navigate(`/${project?.id}/artifacts/${selType}/${selEntity}/${v}`);
  }

  function selectFile(filename: string) {
    setSearchParams((prev) => {
      if (filename) {
        prev.set("file", filename);
      } else {
        prev.delete("file");
      }
      return prev;
    });
  }

  const bibleFileNames = useMemo(() => {
    if (!selectedDetail?.bible_files) return [];
    return Object.keys(selectedDetail.bible_files).sort();
  }, [selectedDetail]);

  const displayData = useMemo(() => {
    if (!selectedDetail) return null;
    if (selectedDetail.artifact_type === "bible_manifest" && selFile && selectedDetail.bible_files) {
      return selectedDetail.bible_files[selFile] || selectedDetail.payload.data;
    }
    return selectedDetail.payload.data;
  }, [selectedDetail, selFile]);

  return (
    <section className="card">
      <h2>Artifacts</h2>
      {!project ? <p className="status-error">Choose or create a project first.</p> : null}
      <button className="secondary" disabled={!project} onClick={() => void loadGroups()}>
        Refresh Artifact Groups
      </button>
      {status.error ? <p className="status-error">{status.error}</p> : null}
      <div className="grid" style={{ marginTop: "8px" }}>
        <div className="card">
          <h3>Groups</h3>
          {groups.map((group) => (
            <button
              key={`${group.artifact_type}-${group.entity_id ?? "project"}`}
              className={`ghost ${
                selectedGroup?.artifact_type === group.artifact_type &&
                (selectedGroup?.entity_id ?? "__project__") === (group.entity_id ?? "__project__")
                  ? "selected"
                  : ""
              }`}
              style={{ marginBottom: "6px" }}
              onClick={() => selectGroup(group)}
            >
              {group.artifact_type}/{group.entity_id ?? "__project__"} v{group.latest_version}
            </button>
          ))}
        </div>
        <div className="card">
          <h3>Versions</h3>
          {versions.map((version) => (
            <button
              key={version.version}
              className={`ghost ${selectedVersion === version.version ? "selected" : ""}`}
              style={{ marginBottom: "6px" }}
              onClick={() => selectVersion(version.version)}
            >
              v{version.version} ({version.health ?? "unknown"})
            </button>
          ))}
        </div>
        {bibleFileNames.length > 0 && (
          <div className="card">
            <h3>Bible Files</h3>
            <button
              className={`ghost ${!selFile ? "selected" : ""}`}
              style={{ marginBottom: "6px" }}
              onClick={() => selectFile("")}
            >
              (Manifest)
            </button>
            {bibleFileNames.map((name) => (
              <button
                key={name}
                className={`ghost ${selFile === name ? "selected" : ""}`}
                style={{ marginBottom: "6px" }}
                onClick={() => selectFile(name)}
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </div>
      {selectedDetail ? (
        <div className="card">
          <h3>Artifact Metadata Summary</h3>
          <ArtifactMetadataSummary detail={selectedDetail} />
        </div>
      ) : null}
      {selectedDetail?.artifact_type === "entity_graph" && (
        <div className="card">
          <h3>Entity Relationship Graph</h3>
          <EntityGraphViewer data={displayData} />
        </div>
      )}
      {selectedDetail ? (
        <div className="card">
          <h3>Artifact JSON {selFile ? `(${selFile})` : "(Manifest)"}</h3>
          <pre className="code">{JSON.stringify(displayData, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

function RunOutcomeSummary({ runState, isPolling }: { runState: RunStateResponse; isPolling: boolean }) {
  const stageEntries = Object.entries(runState.state.stages);
  const failedStage = stageEntries.find(([, stage]) => stage.status === "failed");
  const producedRefs = stageEntries.reduce((count, [, stage]) => count + stage.artifact_refs.length, 0);
  const params = runState.state.runtime_params || {};

  return (
    <div style={{ marginTop: "12px", borderTop: "1px solid #eee", paddingTop: "8px" }}>
      <p>
        Produced artifact refs: <strong>{producedRefs}</strong>
      </p>
      {failedStage ? (
        <p className="status-error">
          Failed stage: <strong>{failedStage[0]}</strong>
        </p>
      ) : (
        <p className="status-ok">No failed stage detected.</p>
      )}
      {runState.background_error && (
        <p className="status-error" style={{ fontSize: "0.85em", marginTop: "4px" }}>
          Error: {runState.background_error}
        </p>
      )}
      {isPolling ? <p className="small muted italic">Polling for updates...</p> : null}
      <details className="small" style={{ marginTop: "8px" }}>
        <summary>Runtime Parameters</summary>
        <pre className="code" style={{ fontSize: "0.8em" }}>
          {JSON.stringify(params, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function ArtifactMetadataSummary({ detail }: { detail: ArtifactDetailResponse }) {
  const payload = detail.payload as {
    metadata?: {
      health?: string;
      lineage?: Array<Record<string, unknown>>;
      cost_data?: { estimated_cost_usd?: number };
      producing_module?: string;
    };
  };
  const metadata = payload.metadata ?? {};
  const lineageCount = metadata.lineage?.length ?? 0;
  const costUsd = metadata.cost_data?.estimated_cost_usd;
  return (
    <ul>
      <li>Health: {metadata.health ?? "unknown"}</li>
      <li>Lineage refs: {lineageCount}</li>
      <li>Cost (USD): {typeof costUsd === "number" ? costUsd : "n/a"}</li>
      <li>Producing module: {metadata.producing_module ?? "unknown"}</li>
    </ul>
  );
}

function EntityGraphViewer({ data }: { data: any }) {
  const edges = (data.edges || []) as any[];
  return (
    <div style={{ marginTop: "12px" }}>
      <table className="table" style={{ fontSize: "0.85em" }}>
        <thead>
          <tr>
            <th>Source</th>
            <th>Relationship</th>
            <th>Target</th>
            <th>Confidence</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {edges.map((edge, i) => (
            <tr key={i}>
              <td>
                <small className="muted">{edge.source_type}</small>
                <br />
                <strong>{edge.source_id}</strong>
              </td>
              <td>
                <span className="badge badge-info">{edge.relationship_type}</span>
                <br />
                <small className="muted">{edge.direction}</small>
              </td>
              <td>
                <small className="muted">{edge.target_type}</small>
                <br />
                <strong>{edge.target_id}</strong>
              </td>
              <td>{(edge.confidence * 100).toFixed(0)}%</td>
              <td>
                <ul style={{ margin: 0, paddingLeft: "16px" }}>
                  {(edge.evidence || []).map((ev: string, j: number) => (
                    <li key={j}>{ev}</li>
                  ))}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

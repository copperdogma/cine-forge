import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";

import {
  createProject,
  getArtifact,
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

const DEFAULT_INPUT = "tests/fixtures/sample_screenplay.fountain";
const DEFAULT_MODEL = "mock";

function useProjectSession(): [SessionProject | null, (value: SessionProject | null) => void] {
  const [project, setProject] = useState<SessionProject | null>(() => {
    const raw = localStorage.getItem("operator-console-project");
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as SessionProject;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (!project) {
      localStorage.removeItem("operator-console-project");
      return;
    }
    localStorage.setItem("operator-console-project", JSON.stringify(project));
  }, [project]);

  return [project, setProject];
}

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

export function App() {
  const [project, setProject] = useProjectSession();
  const [seedInputPath, setSeedInputPath] = useState(DEFAULT_INPUT);
  const [recentProjects, setRecentProjects] = useState<RecentProjectSummary[]>([]);
  const [projectsError, setProjectsError] = useState("");
  const [switcherOpen, setSwitcherOpen] = useState(!project);

  async function refreshProjects() {
    setProjectsError("");
    try {
      const projects = await listRecentProjects();
      setRecentProjects(projects);
    } catch (error) {
      if (error instanceof Error) {
        setProjectsError(error.message);
      } else {
        setProjectsError(String(error));
      }
    }
  }

  useEffect(() => {
    void refreshProjects();
  }, []);

  return (
    <div className="container">
      <header className="topbar">
        <div>
          <h1>CineForge Operator Console Lite</h1>
          <p>
            Active project: <strong>{project ? project.label : "(none)"}</strong>
          </p>
        </div>
        <button className="secondary projects-toggle" onClick={() => setSwitcherOpen(true)}>
          Projects
        </button>
      </header>

      {switcherOpen ? (
        <ProjectSwitcher
          activeProject={project}
          projects={recentProjects}
          projectsError={projectsError}
          canClose={Boolean(project)}
          modal={Boolean(project)}
          onClose={() => setSwitcherOpen(false)}
          onActivate={(next, inputPath) => {
            setProject(next);
            if (inputPath) {
              setSeedInputPath(inputPath);
            }
            setSwitcherOpen(false);
          }}
          onRefresh={() => void refreshProjects()}
        />
      ) : null}

      <nav className="nav">
        <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/new">
          New Project
        </NavLink>
        <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/run">
          Run Pipeline
        </NavLink>
        <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/runs">
          Runs / Events
        </NavLink>
        <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/artifacts">
          Artifacts
        </NavLink>
      </nav>

      <Routes>
        <Route
          path="/"
          element={
            <NewProjectPage
              onProjectCreated={(next, inputPath) => {
                setProject(next);
                setSeedInputPath(inputPath);
                setSwitcherOpen(false);
              }}
              refreshProjects={refreshProjects}
            />
          }
        />
        <Route
          path="/new"
          element={
            <NewProjectPage
              onProjectCreated={(next, inputPath) => {
                setProject(next);
                setSeedInputPath(inputPath);
                setSwitcherOpen(false);
              }}
              refreshProjects={refreshProjects}
            />
          }
        />
        <Route path="/run" element={<RunPage project={project} seedInputPath={seedInputPath} />} />
        <Route path="/runs" element={<RunsPage project={project} />} />
        <Route path="/artifacts" element={<ArtifactsPage project={project} />} />
      </Routes>
    </div>
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
      navigate("/run");
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
      navigate("/run");
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
          accept=".fountain,.fdx,.txt,.md,.pdf"
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

function RunPage({ project, seedInputPath }: { project: SessionProject | null; seedInputPath: string }) {
  const [inputFile, setInputFile] = useState(seedInputPath || DEFAULT_INPUT);
  const [defaultModel, setDefaultModel] = useState(DEFAULT_MODEL);
  const [qaModel, setQaModel] = useState(DEFAULT_MODEL);
  const [runMode, setRunMode] = useState<"accept" | "review">("accept");
  const [runId, setRunId] = useState<string>("");
  const [runState, setRunState] = useState<RunStateResponse | null>(null);
  const [draftDetail, setDraftDetail] = useState<ArtifactDetailResponse | null>(null);
  const [draftEdit, setDraftEdit] = useState<Record<string, unknown> | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const status = useAsyncError();

  useEffect(() => {
    setInputFile(seedInputPath || DEFAULT_INPUT);
  }, [seedInputPath]);

  useEffect(() => {
    if (!runId) {
      return;
    }
    const timer = window.setInterval(() => {
      void getRunState(runId)
        .then((result) => setRunState(result))
        .catch(() => {
          // ignore transient polling errors in view loop
        });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [runId]);

  const stageRows = useMemo(() => {
    if (!runState) {
      return [];
    }
    return Object.entries(runState.state.stages);
  }, [runState]);

  async function start(acceptConfig: boolean, configOverrides?: Record<string, unknown>) {
    if (!project) {
      status.from(new Error("Choose or create a project first."));
      return;
    }
    status.clear();
    setDraftDetail(null);
    setDraftEdit(null);
    try {
      const started = await startRun({
        project_id: project.id,
        input_file: inputFile,
        default_model: defaultModel,
        qa_model: qaModel,
        accept_config: acceptConfig,
        force: true,
        config_overrides: configOverrides,
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
    for (let attempt = 0; attempt < 10; attempt += 1) {
      try {
        const current = await getRunState(activeRunId);
        setRunState(current);
        return;
      } catch {
        await new Promise((resolve) => window.setTimeout(resolve, 250));
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
          <label htmlFor="default-model">Default Model</label>
          <input
            id="default-model"
            value={defaultModel}
            onChange={(event) => setDefaultModel(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="qa-model">QA Model</label>
          <input id="qa-model" value={qaModel} onChange={(event) => setQaModel(event.target.value)} />
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
      </div>
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
                <th>Duration (s)</th>
                <th>Cost (USD)</th>
              </tr>
            </thead>
            <tbody>
              {stageRows.map(([stageId, stage]) => (
                <tr key={stageId}>
                  <td>{stageId}</td>
                  <td>{stage.status}</td>
                  <td>{stage.duration_seconds}</td>
                  <td>{stage.cost_usd}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <RunOutcomeSummary runState={runState} />
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

function RunsPage({ project }: { project: SessionProject | null }) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
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
  }, [project]);

  async function loadRunData() {
    if (!selectedRunId) {
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
          <RunOutcomeSummary runState={state} />
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

function ArtifactsPage({ project }: { project: SessionProject | null }) {
  const [groups, setGroups] = useState<ArtifactGroupSummary[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<ArtifactGroupSummary | null>(null);
  const [versions, setVersions] = useState<ArtifactVersionSummary[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<ArtifactDetailResponse | null>(null);
  const status = useAsyncError();

  async function loadGroups() {
    if (!project) {
      return;
    }
    status.clear();
    try {
      const next = await listArtifactGroups(project.id);
      setGroups(next);
      setSelectedDetail(null);
      setSelectedVersion(null);
      if (next.length && !selectedGroup) {
        setSelectedGroup(next[0]);
      }
    } catch (error) {
      status.from(error);
    }
  }

  useEffect(() => {
    void loadGroups();
  }, [project]);

  useEffect(() => {
    if (!project || !selectedGroup) {
      return;
    }
    const entityId = selectedGroup.entity_id ?? "__project__";
    void listArtifactVersions(project.id, selectedGroup.artifact_type, entityId)
      .then((next) => {
        setVersions(next);
        if (!next.length) {
          setSelectedVersion(null);
          setSelectedDetail(null);
          return;
        }
        const latest = next[next.length - 1];
        setSelectedVersion(latest.version);
        void loadDetail(latest.version);
      })
      .catch((error: unknown) => status.from(error));
  }, [project, selectedGroup]);

  async function loadDetail(version: number) {
    if (!project || !selectedGroup) {
      return;
    }
    status.clear();
    try {
      const entityId = selectedGroup.entity_id ?? "__project__";
      const detail = await getArtifact(project.id, selectedGroup.artifact_type, entityId, version);
      setSelectedVersion(version);
      setSelectedDetail(detail);
    } catch (error) {
      status.from(error);
    }
  }

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
                selectedGroup?.entity_id === group.entity_id
                  ? "selected"
                  : ""
              }`}
              style={{ marginBottom: "6px" }}
              onClick={() => {
                setSelectedGroup(group);
                setSelectedVersion(null);
                setSelectedDetail(null);
              }}
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
              onClick={() => void loadDetail(version.version)}
            >
              v{version.version} ({version.health ?? "unknown"})
            </button>
          ))}
        </div>
      </div>
      {selectedDetail ? (
        <div className="card">
          <h3>Artifact Metadata Summary</h3>
          <ArtifactMetadataSummary detail={selectedDetail} />
        </div>
      ) : null}
      {selectedDetail ? (
        <div className="card">
          <h3>Artifact JSON</h3>
          <pre className="code">{JSON.stringify(selectedDetail.payload, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

function RunOutcomeSummary({ runState }: { runState: RunStateResponse }) {
  const stageEntries = Object.entries(runState.state.stages);
  const failedStage = stageEntries.find(([, stage]) => stage.status === "failed");
  const producedRefs = stageEntries.reduce((count, [, stage]) => count + stage.artifact_refs.length, 0);

  return (
    <div>
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

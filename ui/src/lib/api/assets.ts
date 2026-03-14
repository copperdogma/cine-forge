import { API_BASE, request, requestFormData } from './core'

export type AssetType = 'image' | 'audio' | 'video' | 'document' | 'other'
export type AssetLockStatus = 'soft_locked' | 'hard_locked' | 'unlocked'
export type AssetTargetKind = 'character' | 'location' | 'prop' | 'scene' | 'project'

export interface InjectedAsset {
  asset_id: string
  filename: string
  asset_type: AssetType
  purpose: string
  entity_type: string | null
  entity_id: string | null
  lock_status: AssetLockStatus
  file_path: string
  file_size_bytes: number
  injected_at: string
  content_type: string | null
  thumbnail_path: string | null
  waveform_path: string | null
  duration_seconds: number | null
  width: number | null
  height: number | null
  tags: string[]
  extra_metadata: Record<string, unknown>
}

export interface InjectedAssetManifest {
  target_kind: AssetTargetKind
  target_id: string
  display_name: string
  assets: InjectedAsset[]
  version: number
  created_at: string
}

export interface InjectAssetParams {
  target_kind: AssetTargetKind
  target_id: string
  purpose: string
  lock_status?: AssetLockStatus
  file: File
}

export interface UpdateAssetLockParams {
  target_kind: AssetTargetKind
  target_id: string
  asset_id: string
  lock_status: AssetLockStatus
  rationale: string
}

export interface ProposeAssetLockChangeParams {
  target_kind: AssetTargetKind
  target_id: string
  asset_id: string
  source_role: string
  proposed_lock_status: AssetLockStatus
  rationale: string
  confidence?: number
}

export interface RespondToAssetLockProposalParams {
  suggestion_id: string
  decision: 'accept' | 'reject'
  decided_by?: string
  reason: string
}

export async function getInjectedAssetManifest(
  projectId: string,
  targetKind: AssetTargetKind,
  targetId: string,
): Promise<InjectedAssetManifest> {
  return request<InjectedAssetManifest>(
    `/api/projects/${projectId}/assets/${targetKind}/${targetId}`,
  )
}

export function injectAsset(
  projectId: string,
  params: InjectAssetParams,
): Promise<InjectedAssetManifest> {
  const form = new FormData()
  form.append('target_kind', params.target_kind)
  form.append('target_id', params.target_id)
  form.append('purpose', params.purpose)
  form.append('lock_status', params.lock_status ?? 'soft_locked')
  form.append('file', params.file)

  return requestFormData<InjectedAssetManifest>(
    `/api/projects/${projectId}/assets/inject`,
    form,
    { method: 'POST' },
  )
}

export function updateInjectedAssetLock(
  projectId: string,
  params: UpdateAssetLockParams,
): Promise<InjectedAssetManifest> {
  return request<InjectedAssetManifest>(
    `/api/projects/${projectId}/assets/${params.target_kind}/${params.target_id}/${params.asset_id}/lock`,
    {
      method: 'POST',
      body: JSON.stringify({
        lock_status: params.lock_status,
        rationale: params.rationale,
      }),
    },
  )
}

export function proposeAssetLockChange(
  projectId: string,
  params: ProposeAssetLockChangeParams,
): Promise<{ suggestion_id: string }> {
  return request<{ suggestion_id: string }>(
    `/api/projects/${projectId}/assets/${params.target_kind}/${params.target_id}/${params.asset_id}/propose-lock-change`,
    {
      method: 'POST',
      body: JSON.stringify({
        source_role: params.source_role,
        proposed_lock_status: params.proposed_lock_status,
        rationale: params.rationale,
        confidence: params.confidence ?? 0.8,
      }),
    },
  )
}

export function respondToAssetLockProposal(
  projectId: string,
  params: RespondToAssetLockProposalParams,
): Promise<{ suggestion_id: string; decision: 'accept' | 'reject'; target_version: string }> {
  return request<{ suggestion_id: string; decision: 'accept' | 'reject'; target_version: string }>(
    `/api/projects/${projectId}/assets/lock-proposals/${params.suggestion_id}/respond`,
    {
      method: 'POST',
      body: JSON.stringify({
        decision: params.decision,
        decided_by: params.decided_by ?? 'human',
        reason: params.reason,
      }),
    },
  )
}

export function getAssetFileUrl(projectId: string, relativePath: string): string {
  const encoded = relativePath
    .split('/')
    .map(part => encodeURIComponent(part))
    .join('/')
  return `${API_BASE}/api/projects/${projectId}/assets/file/${encoded}`
}

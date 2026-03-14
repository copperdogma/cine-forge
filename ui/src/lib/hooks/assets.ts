import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getInjectedAssetManifest,
  injectAsset,
  proposeAssetLockChange,
  respondToAssetLockProposal,
  updateInjectedAssetLock,
} from '../api'
import type {
  AssetTargetKind,
  InjectAssetParams,
  ProposeAssetLockChangeParams,
  RespondToAssetLockProposalParams,
  UpdateAssetLockParams,
} from '../api'

function assetManifestKey(projectId: string, targetKind: AssetTargetKind, targetId: string) {
  return ['assets', projectId, targetKind, targetId] as const
}

export function useInjectedAssetManifest(
  projectId: string | undefined,
  targetKind: AssetTargetKind | undefined,
  targetId: string | undefined,
) {
  return useQuery({
    queryKey: targetKind && targetId && projectId
      ? assetManifestKey(projectId, targetKind, targetId)
      : ['assets', projectId, targetKind, targetId],
    queryFn: () => getInjectedAssetManifest(projectId!, targetKind!, targetId!),
    enabled: !!(projectId && targetKind && targetId),
  })
}

export function useInjectAsset(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: InjectAssetParams) => injectAsset(projectId, params),
    onSuccess: (_, params) => {
      queryClient.invalidateQueries({
        queryKey: assetManifestKey(projectId, params.target_kind, params.target_id),
      })
    },
  })
}

export function useUpdateInjectedAssetLock(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: UpdateAssetLockParams) => updateInjectedAssetLock(projectId, params),
    onSuccess: (_, params) => {
      queryClient.invalidateQueries({
        queryKey: assetManifestKey(projectId, params.target_kind, params.target_id),
      })
    },
  })
}

export function useProposeAssetLockChange(projectId: string) {
  return useMutation({
    mutationFn: (params: ProposeAssetLockChangeParams) => proposeAssetLockChange(projectId, params),
  })
}

export function useRespondToAssetLockProposal(
  projectId: string,
  targetKind?: AssetTargetKind,
  targetId?: string,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: RespondToAssetLockProposalParams) =>
      respondToAssetLockProposal(projectId, params),
    onSuccess: () => {
      if (!targetKind || !targetId) return
      queryClient.invalidateQueries({
        queryKey: assetManifestKey(projectId, targetKind, targetId),
      })
    },
  })
}

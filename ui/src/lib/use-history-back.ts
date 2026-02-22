import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * Returns a callback that navigates back in browser history if a prior
 * in-app entry exists, otherwise falls back to the given route.
 *
 * This replaces hardcoded `navigate('/some/path')` in back buttons so that
 * cross-entity navigation works correctly (e.g. character → scene → back
 * returns to the character, not the scenes list).
 *
 * Story 068.
 */
export function useHistoryBack(fallbackPath: string): () => void {
  const navigate = useNavigate()
  return useCallback(() => {
    // window.history.length > 1 is the standard heuristic for "there is a
    // prior entry." It's not perfect (the browser counts entries from before
    // the SPA loaded), but it's the accepted approach in React Router apps.
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate(fallbackPath)
    }
  }, [navigate, fallbackPath])
}

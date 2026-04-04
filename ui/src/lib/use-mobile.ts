import { useEffect, useState } from 'react'

const MOBILE_MEDIA_QUERY = '(max-width: 767px)'

function getIsMobile() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false
  }
  return window.matchMedia(MOBILE_MEDIA_QUERY).matches
}

export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(getIsMobile)

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return undefined
    }

    const mediaQuery = window.matchMedia(MOBILE_MEDIA_QUERY)
    const handleChange = (event: MediaQueryListEvent) => {
      setIsMobile(event.matches)
    }

    mediaQuery.addEventListener('change', handleChange)

    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }, [])

  return isMobile
}

import { useEffect, useCallback } from 'react';

/**
 * Keyboard shortcut definition
 */
export interface Shortcut {
  key: string;
  meta?: boolean;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  label: string;
  category?: string;
}

/**
 * Display-only shortcut definition (for help UI)
 */
export interface ShortcutDefinition {
  key: string;
  meta?: boolean;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  label: string;
  category: string;
}

/**
 * Detect if running on macOS
 */
const isMac = typeof navigator !== 'undefined' && navigator.platform.toLowerCase().includes('mac');

/**
 * Format a key combination for display
 */
export function formatShortcut(shortcut: ShortcutDefinition | Shortcut): string {
  const parts: string[] = [];

  if (shortcut.meta) {
    parts.push(isMac ? '⌘' : 'Ctrl');
  }
  if (shortcut.ctrl) {
    parts.push('Ctrl');
  }
  if (shortcut.shift) {
    parts.push('⇧');
  }
  if (shortcut.alt) {
    parts.push(isMac ? '⌥' : 'Alt');
  }

  // Format key display
  let keyDisplay = shortcut.key;
  if (keyDisplay === 'Escape') {
    keyDisplay = 'Esc';
  } else if (keyDisplay.length === 1) {
    keyDisplay = keyDisplay.toUpperCase();
  }

  parts.push(keyDisplay);

  return parts.join(isMac ? '' : '+');
}

/**
 * Check if a keyboard event matches a shortcut definition
 */
function matchesShortcut(event: KeyboardEvent, shortcut: Shortcut): boolean {
  // Normalize key comparison (case-insensitive)
  const eventKey = event.key.toLowerCase();
  const shortcutKey = shortcut.key.toLowerCase();

  if (eventKey !== shortcutKey) {
    return false;
  }

  // Check modifiers
  // meta = Cmd on Mac, Ctrl on Windows/Linux
  const metaPressed = isMac ? event.metaKey : event.ctrlKey;
  const ctrlPressed = event.ctrlKey;
  const shiftPressed = event.shiftKey;
  const altPressed = event.altKey;

  if (shortcut.meta && !metaPressed) return false;
  if (!shortcut.meta && metaPressed && !shortcut.ctrl) return false;

  if (shortcut.ctrl && !ctrlPressed) return false;
  if (!shortcut.ctrl && ctrlPressed && !shortcut.meta) return false;

  if (shortcut.shift && !shiftPressed) return false;
  // Allow shift for keys that inherently require it (e.g., '?' is Shift+/)
  const shiftedKeys = '?!@#$%^&*()_+{}|:"<>~';
  const keyRequiresShift = shiftedKeys.includes(shortcut.key);
  if (!shortcut.shift && !keyRequiresShift && shiftPressed) return false;

  if (shortcut.alt && !altPressed) return false;
  if (!shortcut.alt && altPressed) return false;

  return true;
}

/**
 * Hook to register keyboard shortcuts
 *
 * @example
 * useShortcuts([
 *   { key: 'b', meta: true, action: () => toggleSidebar(), label: 'Toggle sidebar' },
 *   { key: '1', meta: true, action: () => navigate('/pipeline'), label: 'Go to Pipeline' },
 * ])
 */
export function useShortcuts(shortcuts: Shortcut[]) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs, textareas, or contenteditable elements
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Exception: allow Escape to work in inputs
        if (event.key !== 'Escape') {
          return;
        }
      }

      for (const shortcut of shortcuts) {
        if (matchesShortcut(event, shortcut)) {
          event.preventDefault();
          event.stopPropagation();
          shortcut.action();
          break;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
}

/**
 * Global shortcut definitions for the entire app
 * Used for displaying help and documentation
 */
export const GLOBAL_SHORTCUTS: ShortcutDefinition[] = [
  // Navigation
  {
    key: '1',
    meta: true,
    label: 'Go to Pipeline',
    category: 'Navigation',
  },
  {
    key: '2',
    meta: true,
    label: 'Go to Runs',
    category: 'Navigation',
  },
  {
    key: '3',
    meta: true,
    label: 'Go to Artifacts',
    category: 'Navigation',
  },
  {
    key: '4',
    meta: true,
    label: 'Go to Inbox',
    category: 'Navigation',
  },

  // Actions
  {
    key: '/',
    label: 'Global search',
    category: 'Actions',
  },
  {
    key: 'k',
    meta: true,
    label: 'Open command palette',
    category: 'Actions',
  },
  {
    key: 'n',
    meta: true,
    label: 'New run',
    category: 'Actions',
  },
  {
    key: ',',
    meta: true,
    label: 'Open settings',
    category: 'Actions',
  },

  // UI Controls
  {
    key: 'b',
    meta: true,
    label: 'Toggle sidebar',
    category: 'UI Controls',
  },
  {
    key: 'i',
    meta: true,
    label: 'Toggle inspector',
    category: 'UI Controls',
  },
  // Help
  {
    key: '?',
    shift: true,
    label: 'Show keyboard shortcuts',
    category: 'Help',
  },
];

/**
 * Get shortcuts grouped by category for display
 */
export function getShortcutsByCategory(): Record<string, ShortcutDefinition[]> {
  const grouped: Record<string, ShortcutDefinition[]> = {};

  for (const shortcut of GLOBAL_SHORTCUTS) {
    const category = shortcut.category || 'Other';
    if (!grouped[category]) {
      grouped[category] = [];
    }
    grouped[category].push(shortcut);
  }

  return grouped;
}

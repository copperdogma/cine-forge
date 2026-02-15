import { useState } from 'react';
import { Keyboard } from 'lucide-react';
import {
  getShortcutsByCategory,
  formatShortcut,
  useShortcuts,
  type ShortcutDefinition,
} from '@/lib/shortcuts';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';

/**
 * Keyboard shortcuts help dialog
 * Opens with ? or Cmd+/
 */
export function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);

  // Register shortcuts to open this dialog
  // Note: Shift+/ produces event.key='?' on real keyboards but '/' with shiftKey on some automation tools
  useShortcuts([
    {
      key: '?',
      action: () => setIsOpen(true),
      label: 'Show keyboard shortcuts',
      category: 'Help',
    },
    {
      key: '/',
      shift: true,
      action: () => setIsOpen(true),
      label: 'Show keyboard shortcuts',
      category: 'Help',
    },
    {
      key: '/',
      meta: true,
      action: () => setIsOpen(true),
      label: 'Show keyboard shortcuts',
      category: 'Help',
    },
  ]);

  const shortcutsByCategory = getShortcutsByCategory();
  const categories = Object.keys(shortcutsByCategory).sort();

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Keyboard className="size-5 text-muted-foreground" />
            <DialogTitle>Keyboard Shortcuts</DialogTitle>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {categories.map((category, index) => (
            <div key={category}>
              {index > 0 && <Separator className="mb-6" />}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-muted-foreground">
                  {category}
                </h3>
                <div className="grid gap-2">
                  {shortcutsByCategory[category].map((shortcut) => (
                    <ShortcutRow key={shortcut.label} shortcut={shortcut} />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t">
          <p className="text-xs text-muted-foreground text-center">
            Press <kbd className="px-1.5 py-0.5 text-xs font-mono bg-muted/50 rounded border">?</kbd> to show this dialog
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Single shortcut row: label + key combo
 */
function ShortcutRow({ shortcut }: { shortcut: ShortcutDefinition }) {
  const formatted = formatShortcut(shortcut);
  const keys = formatted.split(/(?=[⌘⇧⌥])|(?<=[⌘⇧⌥])/g).filter(Boolean);

  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-foreground">{shortcut.label}</span>
      <div className="flex items-center gap-1">
        {keys.map((key, index) => (
          <kbd
            key={index}
            className="px-2 py-1 text-xs font-mono bg-muted/50 rounded border min-w-[1.75rem] text-center"
          >
            {key}
          </kbd>
        ))}
      </div>
    </div>
  );
}

/**
 * Imperative API to open the shortcuts dialog from anywhere
 * (e.g., from command palette)
 */
export function openKeyboardShortcutsHelp() {
  // This is a placeholder for the imperative API
  // The actual implementation would need to use a global state or event system
  // For now, users can just press Cmd+/ to open it
  console.warn('openKeyboardShortcutsHelp: Use Cmd+/ to open the dialog');
}

# Story 185: dialog lifecycle and persistent operations

2026-10-23. Problem class: asynchronous operations outliving dismissible UI.

Moving an always-mounted assembly card into a dialog initially moved its
TanStack mutation observer into a component that unmounts on dismissal. An
independent review demonstrated with the installed MutationObserver that a new
observer starts idle while the original request remains pending. Since the run
ID arrives only after the POST, reopening could briefly enable duplicate work.

React documents that removing a component discards its state, and recommends
keeping state in a persistent position when it must survive removal:
[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state).
Adopt that standard pattern: `SupportingActions` owns
`useFinalOutputController`; only the card's display mounts in Project Cut.
Do not force hidden dialog portals to remain mounted or add a second run store.

The extraction also hit React's ref inference lint when a mixed data object
contained an editor ref. The [refs rule](https://react.dev/reference/eslint-plugin-react-hooks/lints/refs)
explains how inference follows values passed through JSX refs. Keep the actual
editor ref in the view and pass it separately to the data/scroll hook and editor;
do not disable the lint or read ref contents during render. Targeted ESLint
passed after this change.

Local demonstration: a browser request interception paused the actual assembly
POST before the backend. Closing and reopening Project Cut retained a disabled
assembly button; an intercepted failure then re-enabled it. Exactly one paused
request was observed. No provider call or pipeline run occurred in that probe.
See `docs/reports/story-185-project-home-hierarchy/assembly-pending-regression.json`.
The debugger follows the standard
[CDP Fetch interception protocol](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/),
using an explicit Fetch resource type and clearing interception with an empty
pattern list as required by this browser host.

This is UI lifecycle proof, not evidence about media quality, backend concurrent
run arbitration, or cross-page pending state. The previous card's page-level
lifetime is preserved; global run-start coordination is a separate concern.

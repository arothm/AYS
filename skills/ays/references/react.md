# React

Load only when the project uses React (a react dependency or .jsx/.tsx
components). Also load `web-javascript.md` and `web-html.md`. Each rule's "Why"
is the reason to follow it; use it to judge cases the rule does not spell out.

## Components and JSX

- `RCT-001` DO wrap adjacent sibling JSX elements in a Fragment (<>...</>) instead of an extra <div>, and never return multiple root-level JSX nodes from a component without a fragment or parent element
  - Why: A component must return one node; a fragment groups siblings without adding a wrapper div that can break flex, grid or table structure.
- `RCT-002` DO name components in PascalCase (e.g., YouTubeComponent) and name their files to match, because JSX treats lowercase-leading names as HTML elements and will not render your component
  - Why: <myComponent> renders an unknown HTML element instead of your component, and matching file names make components easy to find.
- `RCT-003` DO use the .jsx (or .tsx) extension for every file that contains JSX in Vite React projects, because Vite does not parse JSX in .js files by default
  - Why: JSX in a .js file fails to parse, so the build or dev server errors out.
- `RCT-004` DON'T put statements (if, for, switch) inside JSX curly braces, because only expressions are allowed there; use a ternary, &&, or .map(), or compute the value before the return
  - Why: A statement inside braces is a syntax error, because JSX braces only accept expressions.
- `RCT-009` DO destructure props in the component's parameter list and set defaults there (e.g., { role = "Guest" }) instead of scattering fallback checks such as props.user || "Default" through the JSX; defaults apply only to undefined, not to null
  - Why: Defaults in the signature document every prop in one place; a null still gets through, so handle it explicitly where it can occur.
- `RCT-010` DO pass numbers, booleans, objects, arrays, and functions as props inside curly braces (e.g., count={5}), since quoted attribute values are always strings
  - Why: count="5" passes the string "5", so math and comparisons quietly go wrong.
- `RCT-018` DO give list items stable, unique keys (e.g., database IDs), and avoid array indexes as keys when the list can reorder, insert, or delete items
  - Why: Keys tell React which item is which; with index keys, reordering mixes up item state and typed input.

## Project setup and libraries

- `RCT-005` DO bootstrap a new React single-page app with Vite (npm create vite@latest) or a framework's own CLI, and never with create-react-app, which is deprecated
  - Why: create-react-app is deprecated and unmaintained, while Vite is fast and current.
- `RCT-006` DO remove the default boilerplate CSS that the Vite React template ships (App.css and index.css, which center content and limit the #root width) before applying your own layout, so full-width layouts, including Tailwind containers, are not constrained
  - Why: The template's CSS centers and caps #root, which silently limits every layout you build on top.
- `RCT-007` DO choose state-management and routing libraries (e.g., Zustand, React Router) according to the project's actual needs, and keep using the libraries the project already has instead of adding or swapping them without being asked
  - Why: The right library depends on what the project needs, and swapping an existing one unasked is expensive churn.

## Hooks and state

- `RCT-008` DON'T add useMemo, useCallback, or React.memo by default; with React Compiler enabled, let it memoize automatically, and use these hooks only as deliberate escape hatches where measurement shows a need or a stable reference is required (e.g., an effect dependency)
  - Why: Manual memoization adds code and is often applied wrongly; React Compiler memoizes automatically and more precisely.
- `RCT-011` DON'T create inline object, array, or function literals in props passed to memoized children or used as hook dependencies, because each render creates a new reference that defeats memoization and re-triggers effects; hoist constants or memoize where it matters
  - Why: A new literal on every render looks like a changed value, so memoized children re-render and effects run again.
- `RCT-012` DO call hooks only at the top level of function components and custom hooks, never inside conditions, loops, or nested functions
  - Why: React matches hooks to their state by call order; a conditional call shifts that order and mixes up state between hooks.
- `RCT-013` DO use the functional updater form (setCount(prev => prev + 1)) whenever the next state depends on the previous state
  - Why: Updates can be batched, so the value in scope may be stale; the updater always receives the latest state.
- `RCT-014` DON'T mutate state or props directly (count = 5, or pushing into an array held in state); update state only through its setter, and create new objects or arrays (spread, map, filter) for changes
  - Why: React detects changes by reference; mutating in place keeps the same reference, so the screen does not update.
- `RCT-015` DO list every reactive value that an effect or callback uses in its dependency array (enforce it with eslint-plugin-react-hooks), and don't set state inside an effect in a way that retriggers the same effect; derive values during render or guard the update to avoid infinite re-render loops
  - Why: A missing dependency leaves the effect using stale values, and setting state that retriggers the effect loops forever.
- `RCT-016` DO use useRef instead of useState for values that do not affect the rendered output (timer IDs, previous values, DOM nodes), so changing them does not cause re-renders
  - Why: Changing a ref does not re-render, which is exactly right for values the screen never shows.
- `RCT-017` DO let React batch state updates automatically, and remember that updates apply asynchronously: a value read right after calling a setter is still the old one, so use functional updaters, derived values, or effects instead of reading it back
  - Why: New state arrives with the next render, so code that reads it right after the setter uses the old value.
- `RCT-022` DO keep functions used by an effect stable: define them inside the effect, move them outside the component if they use no props or state, or wrap them in useCallback when they must appear in the dependency array, to avoid needless effect re-runs
  - Why: A function defined in the component is new every render, so as a dependency it re-runs the effect every time.

## DOM, events and performance

- `RCT-019` DON'T change React-rendered DOM nodes directly (e.g., with document.getElementById); drive changes through state, and when imperative access is truly needed use a ref and check that ref.current exists first (e.g., passwordRef.current?.select())
  - Why: React owns the DOM it renders, so direct changes are overwritten on the next render or leave the screen out of sync with state.
- `RCT-020` DON'T run long synchronous loops or heavy computation on the main thread during animations or user interaction; move them to a Web Worker, split the work into chunks, or defer it (useTransition, useDeferredValue) so the UI stays responsive
  - Why: Long work on the main thread freezes typing, clicks and animation until it finishes.
- `RCT-021` DO wrap state-updating calls that need arguments in an arrow function in event handlers (onClick={() => setColor("red")}), and never call a setter directly in the attribute (onClick={setColor("red")}), which runs during render and causes a "too many re-renders" error
  - Why: onClick={setColor("red")} calls the setter while rendering, which triggers another render, endlessly.

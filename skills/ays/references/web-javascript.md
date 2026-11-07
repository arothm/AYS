# Web — JavaScript

Load when writing, reviewing or fixing client-side or Node JavaScript/TypeScript.
React projects also load `react.md`; Bun projects also load `bun.md`. Each
rule's "Why" is the reason to follow it; use it to judge cases the rule does not
spell out.

## Role of JavaScript

- `WEB-004` Do not expect interactive behavior beyond what HTML provides natively (links, form submission, <details>, <dialog>, popover) without the behavioral layer of JavaScript; use the native element first and add JavaScript only for what it cannot do (see WEB-259)
  - Why: Native elements already handle keyboard, focus and accessibility; re-implementing them in JavaScript adds code and bugs, while behavior beyond them does need a script.
- `WEB-141` DO treat JavaScript as an enhancement layer that builds upon a solid HTML/CSS foundation
  - Why: If the script fails or loads slowly, the HTML and CSS still work, so the page degrades instead of breaking.
- `WEB-142` DO use the <script> element as the mandatory vehicle for triggering all client-side logic
  - Why: Browsers only run JavaScript that a script element (or a module it imports) loads; code anywhere else never executes.
- `WEB-143` DO architect your scripts with the understanding that they must interact with the browser's DOM construction
  - Why: A script that looks up elements before the parser has created them finds nothing and fails with null errors.
- `WEB-144` DON'T over-engineer; remember that many high-quality sites function perfectly with minimal or no scripting
  - Why: Every script costs download, parsing and maintenance; content that works without it is faster and more robust.
- `WEB-145` DON'T expect the browser to automatically detect or execute standalone logic without a proper HTML reference
  - Why: A .js file on the server does nothing until a page references it with a script tag or an import.
- `WEB-146` DON'T disregard the relationship between script execution and the physical order of HTML tags in your source code
  - Why: A classic script runs where it appears and sees only the elements above it, and script order decides what is already defined.
- `WEB-259` DO build features with native browser APIs before adding libraries or frameworks, and evaluate whether a framework is needed at all (e.g., do not load jQuery for simple DOM queries); simple, static, content-driven sites usually do better with plain HTML/CSS/JS or a lightweight option (e.g., Astro, HTMX) than with a client-side framework such as React
  - Why: Native APIs cost no download and no dependency to update; a framework only pays for its weight when the interface is genuinely interactive.

## Loading scripts

- `WEB-147` DO move the vast majority of your logic into external .js files to facilitate browser caching and cleaner code organization
  - Why: External files are cached across pages and can be deferred; inline code is downloaded again with every page.
- `WEB-148` DO reserve inline scripts for tiny, critical tasks that must run before first paint or before any network requests (e.g., applying a saved theme to prevent a flash of the wrong theme)
  - Why: These must run before anything is shown; waiting for an external file would cause a visible flash.
- `WEB-149` DO use clear, descriptive filenames for your external scripts to make troubleshooting easier for the engineering team
  - Why: Descriptive names make network logs, stack traces and the source tree readable while debugging.
- `WEB-150` DON'T clutter your HTML templates with large blocks of JavaScript; this makes the document difficult to read and nearly impossible to cache efficiently
  - Why: Large inline scripts cannot be cached, mix concerns, and make a Content-Security-Policy harder to apply.
- `WEB-151` DON'T forget the src attribute when attempting to link external logic, and ensure your file paths are accurate
  - Why: Without src the tag runs its empty body, so nothing loads and no error appears; a wrong path only shows as a 404.

## Language

- `WEB-228` DO use const by default and let only when reassignment is required
  - Why: const prevents accidental reassignment and tells the reader the binding never changes; let marks the ones that do.
- `WEB-229` DO use "use strict" at the top of legacy (non-module) scripts, or use ES modules, which are strict by default
  - Why: Strict mode turns silent mistakes, such as assigning to an undeclared variable, into errors you can see.
- `WEB-230` DO use strict equality operators (=== and !==) to avoid implicit type coercion bugs
  - Why: == converts types with surprising results ("0" == false is true); === compares without converting.
- `WEB-231` DO use the nullish coalescing operator (??) for default values so valid falsy values like 0 and "" are kept (unlike ||)
  - Why: || replaces every falsy value, so a legitimate 0 or empty string becomes the default; ?? replaces only null and undefined.
- `WEB-232` DON'T pollute the global scope; use ES modules, block scope, or closures
  - Why: Globals collide with other scripts and libraries and can be changed from anywhere, which makes bugs hard to trace.
- `WEB-233` DON'T use var; use const or let
  - Why: var is function-scoped and hoisted, which causes bugs in loops and blocks; let and const are block-scoped.
- `WEB-234` DON'T mutate object parameters passed into functions (including React props, which are read-only); work on a copy (e.g., structuredClone or spread) when changes are needed
  - Why: The caller still holds the same object, so the change appears somewhere far away; mutating React props also breaks rendering.
- `WEB-235` DON'T write obfuscated or "ninja code" shortcuts that hide the intent of the code
  - Why: Clever short code saves seconds when written and costs far more every time someone reads or debugs it.
- `WEB-236` DON'T modify native prototypes (Array.prototype, Object.prototype) directly, as it risks global side effects and library collisions (spec-compliant polyfills are the exception)
  - Why: Every script on the page shares them, so a change can break libraries and clash with methods added to the language later.
- `WEB-253` DO use arrow functions where lexical this is needed (callbacks, handlers) instead of manually binding this, and use regular methods when you need dynamic this
  - Why: Arrow functions take this from the surrounding code, so callbacks keep the right this without bind; methods need this to be the object they are called on.
- `WEB-263` DON'T mutate state arrays when sorting; use toSorted() or sort a copy ([...items].sort())
  - Why: sort() reorders the original array in place, so state shared with other code changes under it, and React does not see the change.
- `WEB-274` DO use top-level await in ES modules instead of wrapping async code in an IIFE; it only works in modules (not CommonJS) and delays every module that imports it, so avoid long awaits in widely imported modules
  - Why: It is clearer than an async IIFE, but every importing module waits for it, so a slow await delays the whole app.
- `WEB-275` DO write comments that explain why the code does something (intent, constraints, non-obvious decisions), not what it does; don't add trivial line-by-line comments such as counter = counter + 1 // Increment counter
  - Why: The code already says what it does; the reason behind it is what gets lost and what the next developer needs.

## DOM

- `WEB-030` Do use firstElementChild (and children, nextElementSibling) when traversing the DOM for elements
  - Why: These skip text and comment nodes, so they return the element you expect.
- `WEB-033` Don't assume firstChild is an element; it is often a whitespace text node created by source formatting
  - Why: Code that expects an element gets a text node and fails when it reads element properties.
- `WEB-177` DON'T mutate element layout properties repeatedly inside fast JavaScript loops or interleave layout reads (e.g., offsetWidth) with style writes (layout thrashing), as this forces the browser to re-run expensive viewport geometry calculations; batch all reads first, then all writes
  - Why: Each read after a write forces an immediate layout recalculation; in a loop that multiplies into dropped frames.
- `WEB-260` DO use event delegation (one listener on a parent) for large or dynamic lists of child elements
  - Why: One listener handles every child, including ones added later, and uses less memory than one listener per item.
- `WEB-262` DO write clear, commented calculations when computing dynamic layout offsets, and prefer CSS solutions (sticky, grid, anchor positioning) over JavaScript math when possible
  - Why: Layout math in JavaScript breaks when fonts, content or the viewport change, while CSS adapts by itself; comments explain any math that remains.
- `WEB-267` DON'T run repeated DOM queries inside loops; cache the results before iterating
  - Why: Each query searches the document again; querying once before the loop avoids repeating that work.

## Async, errors and network

- `WEB-172` DO use AbortController (or your HTTP client's cancel feature) to cancel requests the user no longer needs, such as when a component unmounts or a newer request replaces the old one; this cancels one response without closing the connection (an RST_STREAM frame under HTTP/2, a RESET_STREAM/STOP_SENDING pair under HTTP/3)
  - Why: Uncancelled requests keep downloading, and an outdated response can arrive last and overwrite newer data on screen.
- `WEB-247` DO handle all promise rejections with .catch() or global handlers (unhandledrejection in browsers, process.on("unhandledRejection") in Node) to prevent silent failures and crashes
  - Why: An unhandled rejection disappears silently in browsers and crashes a Node process by default.
- `WEB-249` DO wrap awaited asynchronous operations in try...catch blocks when using async/await
  - Why: A rejected await throws; without try/catch the error escapes your code and is lost or crashes the caller.
- `WEB-251` DON'T spawn infinite microtask loops (e.g., recursive queueMicrotask calls); they starve macrotask processing and freeze the page
  - Why: Microtasks run before any rendering or input handling, so an endless chain blocks the page completely.
- `WEB-252` DON'T mix callback-style APIs with Promises without explicit promisification
  - Why: Errors fall through the gap between callback and promise handling; converting once and using one style keeps them caught.
- `WEB-265` DON'T rely on setInterval ticks to keep accurate time, because they drift; compute from absolute timestamps (Date.now() or performance.now())
  - Why: Timers are delayed by a busy thread and throttled in background tabs, so counting ticks drifts from real time.
- `WEB-276` DO set a timeout on every outbound network request (e.g., AbortSignal.timeout() or the HTTP client's timeout option) and catch transport errors, so a slow or failing endpoint cannot hang the caller (see WEB-172)
  - Why: Without a timeout one stuck request can hold the interface or a worker for minutes.

## Memory and lifecycle

- `WEB-248` DO clear intervals and timeouts (clearInterval, clearTimeout) and remove listeners and references you no longer need, to prevent memory leaks (in React, return a cleanup function from useEffect)
  - Why: Forgotten timers and listeners keep running and keep their objects in memory, so memory grows and old handlers fire on UI that is gone.
- `WEB-250` DO use WeakMap or WeakSet when caching data or metadata tied to DOM nodes or short-lived objects, so they can be garbage-collected
  - Why: Weak keys do not keep their objects alive, so the cache entry disappears when the node or object does.
- `WEB-254` DON'T store heavy data in unbounded global collections; cap their size or evict old entries
  - Why: An unbounded collection grows until the tab or process runs out of memory.
- `WEB-264` DON'T leave continuous hardware tracking active (e.g., geolocation watchPosition, device sensors) when the user leaves the tab; stop it with clearWatch or the Page Visibility API
  - Why: Background tracking drains the battery and keeps reading the user's location while they are not using the page.
- `WEB-269` DON'T leave global window or document event listeners attached when removing dynamic UI; remove them (removeEventListener or an AbortSignal)
  - Why: Global listeners outlive the removed UI, keep it in memory, and keep firing on elements that no longer exist.

## Storage and secrets

- `WEB-258` DON'T expose server secrets or tokens in client-side JavaScript bundles; anything shipped to the browser is public, including values with public prefixes such as NEXT_PUBLIC_ or VITE_, and sensitive system-prompt logic or infrastructure configuration placed in client-side code or text
  - Why: Anyone can read a bundle in devtools; those prefixes mark values that get shipped, so a secret placed there is published.
- `WEB-266` DO store high-volume structured offline data in IndexedDB instead of localStorage, which is synchronous, string-only, and size-limited
  - Why: localStorage blocks the main thread, stores only strings and holds about 5 MB; IndexedDB is asynchronous, structured and far larger.
- `WEB-268` DON'T store sensitive authentication tokens in localStorage, where XSS can read them; prefer HttpOnly, Secure, SameSite cookies
  - Why: Any injected script can read localStorage, but HttpOnly cookies are out of JavaScript's reach.

## Dependencies, structure and build output

- `WEB-255` DO audit third-party dependency trees regularly (e.g., npm audit or an automated dependency scanner) to catch known vulnerabilities such as remote code execution flaws in utility libraries
  - Why: A known vulnerability in a dependency is the easiest way into an app; an audit finds it before an attacker does.
- `WEB-256` DO organize code into modules with clear boundaries and single responsibilities, without speculative abstraction (see WEB-144)
  - Why: Clear boundaries keep each change local, while abstractions built for imagined future needs add complexity that rarely pays off.
- `WEB-257` DON'T install unvetted third-party micro-packages (e.g., is-even-ai) for trivial logic that built-in language features can handle
  - Why: Each tiny package is one more supply-chain risk and update to track, for something one line of code does.
- `WEB-272` DON'T edit generated or compiled output (e.g., build/ or dist/ CSS and JS) by hand; make every change in the source files and rebuild
  - Why: The next build overwrites generated files, so hand edits vanish and the source no longer matches what shipped.

## Interaction and accessibility

- `WEB-152` DO test your entire interface using only a keyboard to ensure no functionality is trapped behind mouse-only events, including animated drawers, menus, and modals (they must open and close from the keyboard, close with Escape, move focus inside when open, and return focus afterwards)
  - Why: Many people rely on the keyboard alone; anything that needs a mouse locks them out (WCAG 2.1.1 and 2.4.3).
- `WEB-153` DO provide explicit "Stop" or "Cancel" controls for any moving content that exceeds a few seconds in duration
  - Why: Moving content distracts users with attention or vestibular disorders, and WCAG 2.2.2 requires a way to pause it.
- `WEB-154` DO provide a <noscript> alternative as a safety net, but don't use it as an excuse for poor primary script design
  - Why: When scripts fail or are blocked, it tells users what is missing instead of showing a blank page.
- `WEB-155` DON'T rely on "assumed" user speed; always permit users to extend or ignore time limits
  - Why: People read and type at very different speeds, and fixed limits lock out users with disabilities (WCAG 2.2.1).
- `WEB-156` DON'T initiate auto-redirects or content refreshes that could disorient users who rely on assistive technologies
  - Why: An unexpected change moves a screen reader's reading position, so the user loses their place.
- `WEB-261` DO request camera, microphone, or geolocation access only in response to a user action, explain why it is needed, and handle denial gracefully
  - Why: Prompts on page load get denied by reflex and browsers may stop showing them; asked in context with a reason, users agree.

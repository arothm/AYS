# Web — Delivery, performance and testing

Load when serving, deploying, optimizing or testing a website, or when checking
its network traffic, protocols, security headers or dependencies. Each rule's
"Why" is the reason to follow it; use it to judge cases the rule does not spell
out.

## Protocols and transport

- `WEB-021` Use HTTP/2 at minimum and HTTP/3 wherever the server or host supports it, including on edge CDNs; HTTP/2 multiplexing removes HTTP-level head-of-line blocking, and HTTP/3 (QUIC) also removes the transport-level blocking that remains over TCP
  - Why: Multiplexing loads many assets in parallel over one connection, and HTTP/3 also stops one lost packet from stalling every stream.
- `WEB-022` Use HTTPS with TLS 1.2 or higher (prefer TLS 1.3) everywhere, redirect HTTP to HTTPS, and enable HSTS
  - Why: Without HTTPS anyone on the network can read or change the traffic, and HSTS stops the first plain-HTTP request from being hijacked.
- `WEB-173` DON'T implement legacy HTTP/1.1 workarounds such as domain sharding or asset spriting in HTTP/2 or HTTP/3 environments, and avoid inlining large assets (e.g., base64 images) because they cannot be cached separately; small critical CSS/JS inlining is the exception (see WEB-130 and WEB-148)
  - Why: Under HTTP/2 these tricks add connections and break caching for no gain, and large inlined assets are downloaded again with every page.
- `WEB-174` DON'T use HTTP/2 Server Push; Chrome has removed support for it and pushes often duplicate assets already in the client cache, so use <link rel="preload"> or 103 Early Hints instead
  - Why: Push no longer works in Chrome and wasted bandwidth on assets the browser already had; preload and Early Hints get the same head start safely.

## Performance

- `WEB-019` Do not serve massive, raw image files and rely on the browser to resize them. Compress assets before they ever hit the server, and prefer modern formats such as WebP or AVIF
  - Why: Oversized originals waste bandwidth and slow pages, worst on mobile; modern formats are much smaller at the same quality.
- `WEB-031` Do minify HTML for production, and enable Brotli or gzip compression on the server
  - Why: Smaller payloads download faster, and compression often shrinks text assets by 70% or more.
- `WEB-175` DO attach defer (or async) to non-critical external scripts, and never place synchronous <script> tags in the <head>, since they block HTML parsing and delay the first paint
  - Why: A synchronous script in the head stops parsing until it has downloaded and run, so the page stays blank meanwhile.

## Network inspection and testing

- `WEB-005` Utilize the browser DevTools Network tab (or, in automated runs, an automated browser such as Playwright or a DevTools-protocol tool that logs requests and responses) to inspect traffic and monitor the payload size of every HTTP request
  - Why: Payload sizes, failed requests and slow responses only show in the network log, never in the rendered page.
- `WEB-006` Verify that the Content-Type matches the expected resource to avoid parsing errors
  - Why: With the wrong Content-Type browsers refuse or misread the file: scripts are blocked, CSS is ignored, JSON shows as text.
- `WEB-023` Test everything E2E as a real user in a real browser (a built-in browser tool if the environment provides one, otherwise Google Chrome or an automated browser such as Playwright that logs network requests), check the network log after every activity, and produce a testing report to fix every 4xx/5xx error
  - Why: Broken flows, failing requests and bugs between features only appear when the site is used as a person uses it, and a report makes sure each one gets fixed.

## Compatibility and client detection

- `WEB-007` Do not rely on the "User-Agent" string to serve different assets to mobile versus desktop clients; prefer responsive design and feature detection, use Client Hints only as a Chromium-only enhancement (Firefox does not support them), and parse User-Agent only as a last resort, since browsers are reducing the information it exposes
  - Why: User-Agent strings are spoofed, frozen and shrinking, so device guesses fail; feature detection checks what the browser can actually do.
- `WEB-045` DO reference the MDN "Baseline" status to ensure cross-device stability and prevent the use of experimental features in production environments
  - Why: Baseline marks features that work in all major browsers, so using them will not break the site for part of your users.

## Dependencies and updates

- `WEB-024` Always check for the latest stable tool/dependency/server (VPS) software updates/versions, but pin versions with lockfiles to insulate builds against compromised upstream releases, read the changelogs, update deliberately, and test before deploying
  - Why: Updates close security holes, but an unpinned build can pull in a compromised release; pinning and reading changelogs keeps every update a deliberate choice.

## Privacy

- `WEB-178` DO support browser-level privacy signals (e.g., Global Privacy Control) to respect user cookie options without relying on intrusive popups
  - Why: GPC is a legally binding opt-out in some places, such as California, and honoring it respects users without another popup.

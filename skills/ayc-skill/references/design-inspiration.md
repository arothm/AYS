# Design sourcing — reference libraries and how to use them

This is the `frontend` agent's playbook for **aesthetic direction**: when the ask
is "build me a premium minimal site" (or brutalist, editorial, dark-technical…),
this is how you turn a vague adjective into a concrete, original implementation —
using known-good references to calibrate taste, not to copy.

## Rule 0 — learn the principle, never clone the work

This capability exists to raise taste, not to launder someone's design.

- **Study patterns and techniques; reimplement originally.** Take the *principle*
  ("the hero works because one 72px headline sits in 40% whitespace with a single
  accent"), never the artifact. Don't reproduce another company's layout, brand,
  copy, or visual identity as a template.
- **Never copy brand assets** — logos, wordmarks, illustrations, photography,
  custom fonts, or proprietary color systems. That is someone's trademark.
- **Code has a license — verify it, don't assume it** (rule 1). Some sources are
  explicitly copy-paste licensed; others are proprietary. Check the actual license
  before any code enters the project, and record what you verified.
- If the user asks for a **direct clone** of a specific company's site, say plainly
  that you'll build something *inspired by* it instead, and explain why.

## Rule 0.5 — you usually cannot see these sites; don't pretend you can

Be honest about your actual perception (rule 1 again):

- **With a Playwright/browser MCP connected** you can genuinely inspect: navigate,
  screenshot at breakpoints, and read computed styles (type scale, palette,
  spacing rhythm, easing). *Then* you may describe what you observed.
- **With only a text fetcher** you get markdown — copy and information
  architecture, but **no CSS, layout, or motion**. Several of these sites also
  return **HTTP 403** to non-browser agents.
- **With no network at all**, work from the distilled knowledge in this file.
- Never write "I looked at X and it uses Y" unless you actually rendered it. Say
  "working from established patterns for this style" instead. A fabricated design
  rationale is the same failure as a fabricated test result.

## The sources — and which layer each one solves

Match the source to the *layer of the problem*; they are not interchangeable.

### 1. manus.im — aesthetic & composition (premium minimal)
A product site whose whole effect comes from **restraint**: one large confident
headline, generous whitespace around the value proposition, a near-neutral palette,
and a clean footer information architecture. Use it to calibrate *how little* a
premium page needs. Proprietary brand site — **inspiration only, never clone**.

### 2a. Vetted component libraries — `data/component-libraries.csv`
Run `python {skill_dir}/scripts/standards.py --libraries`. Covers **shadcn/ui** (the base
layer; an official MCP exists — prefer it when connected), **Magic UI** and
**Aceternity UI** (animated marketing blocks), **React Bits**, **React Icons**,
and **Google Fonts**. Each row records delivery model, licence, best-for, and
caveats. Three rules bind their use: these are **copy-paste — the code becomes
yours to maintain**; **verify the licence of the exact component** before it
enters the repo (Aceternity in particular has mixed free/paid tiers, and each
React Icons set carries its own licence); and **restyle to the project's tokens**
so the result doesn't look stock. Effect-heavy blocks still have to clear the
performance budget and `prefers-reduced-motion` — measure LCP/INP after adding
one.

**Browse them live when a browser MCP is connected.** With a Playwright/browser
MCP (setup in `testing-harness.md`), the `frontend` agent can actually navigate
these catalogues — `ui.aceternity.com/components`, `reactbits.dev`,
`magicui.design`, `ui.shadcn.com`, `react-icons.github.io/react-icons`,
`fonts.google.com` — view the components against the user's brief, and pull the
ones that fit. The point of doing this per-project is **variety**: pick and adapt
components that match *this* user's ask instead of emitting the same template for
everyone. Then two things bind the result: **licence** — only copy what the
component's licence permits, and record it; and **adaptation** — restyle to the
project's own tokens and often recombine, so it reads as designed *for this
product*, not pasted in (which is also how a hundred users of this skill avoid
shipping the same-looking site). Without a browser MCP, work from the catalogue
above and the distilled knowledge below, and say which you did.

### 2. Watermelon UI (`ui.watermelon.sh`) — component & block implementation
An **open-source, copy-paste component registry**: 260+ React components,
dashboards, and blocks built on **React 19 + Tailwind v4 + Radix UI + Framer
Motion**, shadcn/ui-compatible, where components live in your codebase rather than
behind a package. Use it when you need a well-built *block* (pricing table,
dashboard shell, nav) instead of inventing one. It is designed to be copied —
still **confirm the current license** and keep attribution where required, and
restyle to the project's own tokens so it doesn't look stock.

### 3a. Choosing the animation library
The generator recommends one from `data/motion-libraries.csv` based on the style's
motion character and your `--stack`: **CSS transitions** and the **View
Transitions API** (zero dependency), **Motion** — formerly Framer Motion, MIT,
React/Vue/vanilla — for declarative app UI, layout and exit animations,
**GSAP** for scroll-driven timelines and SVG morphing, **AutoAnimate** for list
changes, **react-spring** for physics, **Lottie** for designer-authored set
pieces, and **R3F/Three.js** for genuine 3D. Each row carries weight, the
`prefers-reduced-motion` approach, SSR notes, and licence. **Cheapest option
that expresses the idea wins** — a dependency must earn its bytes against the
performance budget, and weight figures are tiers to verify against the release
you actually install, not quoted facts.

### 3. GSAP (`gsap.com`) — motion technique
The professional animation library, plus plugins: **ScrollTrigger** (scroll-driven
sequences), **ScrollSmoother**, **SplitText** (per-character/word reveals),
**Flip** (layout-change transitions), **MorphSVG**/**DrawSVG**/**MotionPath**,
**Draggable**, **Observer**, **Inertia**. Use it to *name and implement* a motion
idea precisely rather than hand-rolling brittle keyframes. GSAP's licensing
changed after the Webflow acquisition — **verify the current terms** for the core
and any plugin before depending on it; do not assert them from memory.

### 4. Casberry Particles (`particles.casberry.in`) — hero spectacle / WebGL
A Three.js/WebGL particle playground (20k+ particles per frame; attractors, flow
fields, fractals; real-time parameters; exports code). Use it for a *signature
hero moment* when the brief genuinely calls for spectacle. Read the tool's export
terms before shipping generated code, and see the performance guardrail below —
this is the single easiest way to destroy a page's Core Web Vitals.

## The generator comes first

Before reasoning from scratch, run the bundled composer — it turns a brief into a
concrete, self-verified spec in one command:

```bash
python {skill_dir}/scripts/design_system.py "premium minimal SaaS landing page"
python {skill_dir}/scripts/design_system.py "<brief>" --persist -o .ayc-skill   # design-system/MASTER.md
python {skill_dir}/scripts/design_system.py "<brief>" --page checkout -o .ayc-skill
python {skill_dir}/scripts/design_system.py --validate      # dataset gate; non-zero exit on failure (offline)
python {skill_dir}/scripts/design_system.py --validate --check-fonts   # + probe providers for the families
python {skill_dir}/scripts/design_system.py "<brief>" --stack react   # stack-aware motion-library pick
python {skill_dir}/scripts/design_system.py --list styles   # or palettes | fonts | products | motion
```

It draws on bundled datasets (`data/styles.csv`, `palettes.csv`,
`font-pairings.csv`, `product-rules.csv`) and emits pattern + section order,
tokens as CSS variables with a **measured** contrast ratio per pair, typography
with the correct provider import, effects, anti-patterns, and a checklist.

**Two things make it trustworthy, and you must respect both.** It *measures*
contrast rather than asserting it, and `--validate` proves the dataset's internal
consistency (every declared font family really is in its import URL; every token
pair clears AA). But it is a **starting spec, not gospel**: it prints its own
match confidence, and a keyword matcher can still pick a style that misses the
brief. If the match is weak or the result contradicts the brief, override
(`--style/--palette/--font`) or reason from the sections below. Never ship a
generated palette over a gradient/image without re-verifying contrast against the
*rendered* result.

## Workflow — adjective → implementation

0. **Run the generator** on the brief; keep its spec if the match is sound.
1. **Translate the brief into vocabulary.** "Premium minimal" is not a spec.
   Resolve it into: type scale + weight contrast, palette size, whitespace ratio,
   motion budget, and the one signature moment. Ask the user for the *one* thing
   the page must make someone feel, and what it must not look like.
2. **Check memory first.** If `Design direction` is already recorded (chosen
   aesthetic, tokens, breakpoints), extend it — don't restyle the product on a
   whim. Consistency beats novelty on an existing codebase.
3. **Consult sources at the right layer** — composition from (1), blocks from (2),
   motion from (3), spectacle from (4) — inspecting live only if you actually can.
4. **Distill to principles, then implement in the project's own system.** Express
   everything through the project's design tokens, component conventions, and
   stack. The output should look like it was designed *for this product*, not
   pasted in. Write down *why* each choice serves the brief (mentor rule).
5. **Record the direction** in the memory delta (`Design direction`) so later runs
   and other agents stay consistent.

## Distilled knowledge (works with zero network)

**Premium minimal** — the effect comes from subtraction, not addition:
- **Type:** one family, 2–3 weights. Big jump between display and body (e.g. clamp
  ~3–4.5rem display vs 1rem body); tight display leading (~1.05–1.15), open body
  leading (~1.6); slight negative tracking on large text only.
- **Palette:** near-neutral base (off-white/near-black — pure #fff/#000 reads
  cheap), 1 accent used sparingly. Convey depth with subtle elevation and hairline
  borders rather than heavy shadows.
- **Space:** whitespace *is* the design — a consistent spacing scale, generous
  section padding, and a max content measure (~60–75ch) so text never sprawls.
- **Motion:** few, purposeful, fast (150–300ms UI; ~600–900ms for one hero
  sequence), gentle easing. One signature moment, not motion everywhere.
- **Signature moment:** exactly one — a staggered headline reveal (SplitText), a
  scroll-pinned sequence (ScrollTrigger), or a restrained particle/gradient field.

**Other common briefs, in one line each:**
- *Editorial* — strong serif display, asymmetric grid, generous measure, minimal motion.
- *Dark technical* — near-black base, one saturated accent, monospace accents, precise hairlines, subtle glow.
- *Brutalist* — system fonts, raw borders, high contrast, deliberate misalignment, abrupt transitions.
- *Glass/soft* — layered translucency + blur, soft shadows, pastel gradients; check contrast carefully, it fails AA easily.

## Guardrails that bind this capability

The `frontend` agent owns **Core Web Vitals and WCAG** — those ownerships do not
pause because something looks impressive:

- **Performance budget wins.** A WebGL/particle hero must not regress LCP/INP.
  Lazy-load and code-split the effect, never block first paint, cap particle
  counts and device-pixel-ratio, pause off-screen (`IntersectionObserver`), and
  ship a **static fallback** for low-power devices. If the effect can't fit the
  budget, say so and propose a cheaper equivalent (CSS gradient, static hero).
- **`prefers-reduced-motion` is mandatory**, not optional — provide a genuinely
  reduced (or motionless) path for scroll-jacking, parallax, and particle motion.
- **Contrast still has to pass** (AA baseline) after any glass/gradient/overlay
  treatment — verify against the rendered result, not the intended swatch.
- **Weight is a cost.** Name the kB and the runtime cost of an animation or 3D
  library before adding it; a signature moment isn't worth a 300kB regression on
  a marketing page.

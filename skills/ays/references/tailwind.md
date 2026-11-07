# Tailwind CSS

Load only when the project uses Tailwind (a tailwindcss dependency, an
@import "tailwindcss" or @tailwind directive, or a tailwind.config file). Also
load `web-css.md`. Each rule's "Why" is the reason to follow it; use it to judge
cases the rule does not spell out.

- `TWD-001` DO encapsulate repeated groups of utility classes in components (React, Vue, Web Components) or custom utilities (@utility in Tailwind v4, @layer utilities in v3) instead of copying long class strings across templates or repeating inline style calculations
  - Why: Copied class strings drift apart over time; one component or utility changes everywhere at once.
- `TWD-002` DO use the theme's spacing scale and design tokens (e.g., p-2, p-4, p-8) for consistent visual rhythm, and use arbitrary values (e.g., w-[calc(100%-68px)], bg-[#123456]) only when the scale cannot express the need
  - Why: The scale keeps spacing and color consistent; arbitrary values scattered around bring back the inconsistency Tailwind exists to remove.
- `TWD-003` DO let prettier-plugin-tailwindcss sort utility classes automatically when the project already uses Prettier, instead of ordering them by hand; don't add Prettier or the plugin to a project that does not use them without asking
  - Why: Automatic sorting ends debates and noisy diffs about class order, but adding tools to a project is the owner's decision.
- `TWD-004` DON'T mix physical utilities (pl-4, mr-2) with logical utilities (ps-4, me-2) in internationalized or right-to-left layouts; use logical utilities consistently
  - Why: Logical utilities flip automatically for right-to-left languages such as Arabic; physical ones mixed in stay put and mirror parts of the layout wrongly.
- `TWD-005` DO run the Tailwind build with --watch (or use the framework's dev server or plugin) during local development so CSS rebuilds on every save
  - Why: Without a watcher, new classes have no CSS until the next manual build, so styles look broken while you work.

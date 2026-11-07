# Web — CSS

Load when writing, reviewing or fixing stylesheets, inline styles or styling in
components. Tailwind projects also load `tailwind.md`. Each rule's "Why" is the
reason to follow it; use it to judge cases the rule does not spell out.

## Stylesheets and the cascade

- `WEB-128` DO use external stylesheets for 100% of site-wide consistency and performance via caching
  - Why: One external stylesheet is downloaded once and cached across every page, and a change happens in one place.
- `WEB-129` DO reserve inline styles only for dynamic JavaScript injections—the main legitimate reason for inline styles in modern apps—or highly restrictive CMS environments, and remember that a strict Content-Security-Policy may block inline styles; don't rely on inline styles to "win" specificity arguments, because as anything but a last resort they make code difficult to manage
  - Why: Inline styles have the highest specificity and cannot be cached or reused, so using them to win starts a specificity war that only !important can end.
- `WEB-130` DON'T use internal styles as the main styling method for projects of more than one page; the exception is a small block of critical CSS inlined in the <head> when it measurably improves first paint
  - Why: A <style> block is downloaded again with every page and copied across pages; only a tiny critical block is worth that cost.
- `WEB-131` DO order your <head> elements intentionally to ensure desired overrides (e.g., placing custom styles after library stylesheets)
  - Why: With equal specificity the later rule wins, so your stylesheet must load after the library's to override it.
- `WEB-133` DO use classes to apply styles to multiple diverse elements (like a span and an li) simultaneously
  - Why: One class styles any element type, so a style is defined once instead of once per tag.
- `WEB-134` DON'T over-complicate selectors if a simple class will suffice, as excessive complexity reduces code readability; avoid long high-specificity chains (e.g., body div.main-wrapper section#hero h1.title) that lock the cascade and make long-term maintenance hard
  - Why: Long chains tie styles to the exact DOM structure and can only be overridden by even longer chains, so every change gets harder.
- `WEB-137` DO use shorthands to keep stylesheets concise and readable
  - Why: Shorthands cut repetition and keep related values, like margin's four sides, together.
- `WEB-138` DON'T forget the specific order of values in shorthands, especially for font and margin
  - Why: A shorthand resets every sub-property you omit and reads values by position, so a mistake silently overrides other rules.
- `WEB-139` DO use comments to mark distinct sections
  - Why: Section comments make long stylesheets navigable and show where a new rule belongs.
- `WEB-140` DON'T compress CSS to the point of unreadability; keep it organized for future updates
  - Why: The source is for people; minifying for production is the build step's job (WEB-031).
- `WEB-210` DON'T include the type="text/css" attribute on <link> or <style> elements; it is unnecessary in HTML5
  - Why: text/css is already the default, so the attribute is noise.
- `WEB-227` DON'T use !important on standard declarations; it breaks the cascade and creates specificity debt, so prefer cascade layers (@layer) and lower-specificity selectors, and reserve !important for utility classes or overriding third-party CSS
  - Why: Each !important forces the next override to use !important too; @layer sets priority deliberately instead.

## Layout

- `WEB-029` Do use Flexbox for one-dimensional layouts (rows or columns) and Grid for two-dimensional layouts
  - Why: Flexbox distributes items along one axis and Grid aligns rows and columns together; forcing either into the other's job needs hacks.
- `WEB-032` Don't rely on inline-block for layouts that need flush alignment, because the whitespace between inline-block elements in the source renders as visible gaps; use Flexbox or Grid instead
  - Why: The gaps change with font size and cannot be removed cleanly, so items never line up flush; Flexbox and Grid have no such gaps.
- `WEB-034` Don't manually strip all whitespace from the source to remove inline-block gaps; fix the layout with Flexbox or Grid and let the production minifier handle whitespace (see WEB-031)
  - Why: Hand-stripped source is unreadable and breaks again the next time someone formats it; the layout tool is the real fix.
- `WEB-219` DO use min-height: 100dvh (with a 100vh fallback) for full-height page containers, because on mobile browsers 100vh is taller than the visible area when toolbars are showing
  - Why: 100vh on mobile includes the area behind the browser toolbars, so content is cut off; dvh follows the visible viewport, and vh covers older browsers.
- `WEB-220` DO give circular elements equal width and height (or aspect-ratio: 1 / 1) before applying border-radius: 50%
  - Why: border-radius: 50% on a non-square box draws an ellipse, not a circle.
- `WEB-221` DON'T set width: 100vw on page wrappers; 100vw includes the vertical scrollbar and causes horizontal overflow, so use width: 100% or auto
  - Why: On desktop the scrollbar makes 100vw wider than the visible page, which adds a sideways scroll.
- `WEB-238` DO use align-self on individual flex items when a specific cross-axis override is needed
  - Why: align-self changes one item's alignment without changing the container's rule for all the others.
- `WEB-240` DO use fr units, repeat(), and grid-template-areas to build clean 2D layouts with CSS Grid
  - Why: These describe the layout directly and readably, without fixed pixel math or extra wrapper elements.
- `WEB-241` DON'T hardcode fixed pixel widths on grid tracks or flex items meant to be responsive; use fr, %, minmax(), or clamp()
  - Why: Fixed widths overflow small screens and leave gaps on large ones; flexible units adapt to the container.
- `WEB-242` DO use display: flow-root on parent containers with floated children to contain the floats, instead of empty clearfix elements such as <div style="clear: both;"></div>
  - Why: One property contains the floats with no extra markup, replacing the clearfix hack.
- `WEB-243` DO use break-inside: avoid on cards or figures, and break-after: avoid on headings, to prevent awkward breaks inside multi-column layouts
  - Why: Without them a card can split across two columns, or a heading can end one column while its text starts the next.
- `WEB-244` DO set position: relative on the parent container when anchoring position: absolute children; otherwise the element is positioned relative to the page or a distant ancestor
  - Why: An absolutely positioned element is placed against its nearest positioned ancestor; without one it attaches to the page.

## Typography and units

- `WEB-213` DO set line-height as a unitless number (e.g., 1.5) so it scales with each element's font size
  - Why: A unitless value is inherited as a ratio, so each element computes its own; a fixed value inherited by larger text makes lines overlap.
- `WEB-216` DO wrap font-family names that contain spaces or special characters in quotes (e.g., "Courier New")
  - Why: Unquoted names with spaces or special characters can be misparsed, and the font silently falls back.
- `WEB-218` DO size typography in rem instead of fixed px so text respects the user's browser default font size (browser zoom works either way)
  - Why: rem follows the default font size the user chose; px ignores it and fails users who need larger text.
- `WEB-222` DON'T use em units for nested font sizes, because they compound down the DOM tree (em remains fine for spacing relative to the element's own font size)
  - Why: em multiplies through nesting, so 1.2em inside 1.2em inside 1.2em keeps growing; rem always refers to the root.
- `WEB-271` DON'T size UI elements that sit alongside text (icons, badges, underline or border indicators) with rigid px offsets; use rem or em so they scale with font size and browser text zoom
  - Why: px decorations stay the same size when text grows, so they end up tiny or misaligned; rem and em keep them in proportion.

## Links, focus and interaction states

- `WEB-135` DO ensure links are visually distinct to provide clear clues to the user
  - Why: Users must be able to see what is clickable; links that look like plain text get missed.
- `WEB-136` DON'T remove underlines or change colors to a point where the link becomes indistinguishable from standard body text
  - Why: WCAG 1.4.1 forbids relying on color alone, so a link that differs only by a faint color fails color-blind users.
- `WEB-211` DO follow the LVFHA order (:link, :visited, :focus, :hover, :active) for anchor pseudo-class rules; any other order lets later states (visited, active) override hover styles
  - Why: These selectors have equal specificity, so source order decides; in the wrong order :visited or :link hides the :hover and :active states.
- `WEB-212` DO pair :focus (or :focus-visible) with every :hover style so keyboard users get the same visual feedback
  - Why: Keyboard users never hover; without a matching focus style they cannot see where they are.
- `WEB-214` DO make navigation links display: block (or flex items) so the whole row is a large click and tap target
  - Why: A large target is easier to hit on touch screens and for users with limited motor control (WCAG 2.5.8).
- `WEB-215` DON'T remove focus outlines (outline: none) without providing a clearly visible alternative focus style for keyboard users
  - Why: The outline is how keyboard users see focus; removing it with no replacement fails WCAG 2.4.7 and makes the page unusable without a mouse.
- `WEB-223` DON'T confuse outline with border; outlines take no layout space and do not change box dimensions
  - Why: Adding a border on hover or focus resizes the element and shifts the layout; an outline draws without moving anything.
- `WEB-270` DO use structural pseudo-classes (:focus-within, :has(), :checked) to manage UI interaction states in CSS before reaching for JavaScript handlers
  - Why: CSS state selectors need no script, cannot fall out of sync with the DOM, and keep working when JavaScript fails.
- `WEB-273` DO set scroll-margin-top on anchor target sections (or scroll-padding-top on the html element) so a fixed or sticky header does not cover the section heading after an anchor jump (Tailwind: scroll-mt-*)
  - Why: Without the offset, the fixed header covers the very heading the user just jumped to.

## Color and contrast

- `WEB-224` DO enforce WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text and UI components) for every color pair, including the hover, focus, active, and checked states of custom form controls (checkbox, radio, select) and dark mode, and verify them with a contrast checker such as WebAIM's before shipping
  - Why: Below these ratios text and controls become unreadable for low-vision users and in bright light, and state colors and dark mode are where contrast most often fails.
- `WEB-226` DO use hsl() or oklch() when adjusting lightness, saturation, or color variations programmatically; alpha can be set directly in hsl(), so the separate hsla() alias is not needed
  - Why: Both separate lightness from hue, so shades can be computed predictably; oklch also keeps perceived lightness even across hues.
- `WEB-239` DO provide a fallback background-color whenever using background-image, so text stays readable if the image fails to load
  - Why: While the image is loading or if it fails, light text over it can become invisible on the default background.

## Resets and form controls

- `WEB-217` DO start stylesheets with box-sizing: border-box on *, *::before, and *::after, and reset default margins and padding deliberately (e.g., with a modern reset), because zeroing every element's spacing also strips useful defaults such as list indentation
  - Why: border-box makes width include padding and border, so sizes add up as expected; a blanket zero reset removes defaults you then rebuild by hand.
- `WEB-225` DO set font: inherit on form elements (input, button, textarea, select), because browsers do not inherit fonts for them by default
  - Why: Form controls use the system font by default, so without it they look out of place next to your text.
- `WEB-237` DO set display: block on images (typically in your reset) to remove the small inline baseline gap beneath them
  - Why: Images are inline by default and sit on the text baseline, leaving a few pixels of gap below that break tight layouts.

## Accessibility helpers

- `WEB-245` DO hide content visually while keeping it available to screen readers with a visually-hidden (sr-only) class (position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap), instead of display: none (which hides it from assistive technology) or large negative offsets like left: -10000px (outdated and problematic in RTL layouts)
  - Why: display: none hides content from screen readers too; this pattern hides it only visually, and negative offsets can create scrolling in right-to-left pages.
- `WEB-246` DO apply scroll-behavior: smooth on the html element only inside @media (prefers-reduced-motion: no-preference)
  - Why: Animated scrolling can cause nausea for people with vestibular disorders, who set the reduced-motion preference to avoid it.

## Animation

- `WEB-176` DO animate with transform and opacity (they avoid layout reflows and can run on the GPU), and use will-change: transform sparingly and only on elements about to animate, since overuse wastes memory
  - Why: Animating width, height or top recalculates layout every frame and stutters; transform and opacity are cheap. Every will-change creates a layer that costs memory.

## Validation and spelling

- `WEB-208` DO validate CSS source files (with the W3C CSS Validation Service or a linter such as Stylelint), because browsers silently drop invalid declarations without console errors, so visual inspection alone will not catch them
  - Why: A typo just means the style never applies, with no error anywhere; only a validator or linter finds it.
- `WEB-209` DO use American English spelling for CSS property names and values (e.g., color, center, gray), because British spellings such as colour or centre are invalid and fail silently
  - Why: CSS only recognizes the American spellings, so colour: red is dropped without any error.

## Merged rules

WEB-132 → WEB-129

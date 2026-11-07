# Web — HTML

Load when writing, reviewing or fixing HTML markup, templates or JSX structure.
IDs keep Abdullrahman's original Web numbering; a missing number was merged into
another rule (listed at the end of this file). Each rule's "Why" is the reason
to follow it; use it to judge cases the rule does not spell out.

## Structure and document

- `WEB-001` Maintain a strict separation of concerns: HTML defines what a piece of content is, CSS defines how it looks (colors, fonts, layouts, animations), and JavaScript defines how it behaves; treat them as separate layers, not interchangeable tools
  - Why: Each layer can then change without breaking the others: a redesign touches only CSS, and screen readers and search engines read meaning from clean HTML.
- `WEB-002` Build a complete structural mental model using HTML before applying styles
  - Why: Styling on top of a weak structure hides semantic mistakes that later break accessibility, SEO and layout; the right structure also makes the CSS simpler.
- `WEB-003` Do not use HTML for visual styling
  - Why: Presentational HTML (font, center, bgcolor, spacer tables) is obsolete, cannot be themed or made responsive, and mixes meaning with looks.
- `WEB-008` Remember that while HTML is not case-sensitive, lowercase tags are the non-negotiable professional standard
  - Why: Lowercase is what validators, XHTML/SVG and JSX expect (JSX treats lowercase names as HTML elements), and mixed case reads as careless.
- `WEB-009` Ensure every non-void element is properly closed with both its opening and closing tag (including <div>, <span>, and <iframe>, whose end tag is mandatory) to prevent "document bleed," where styles or logic apply to unintended areas
  - Why: An unclosed element makes the parser guess where it ends, so later content inherits its styles, layout or event handlers in ways that are hard to trace.
- `WEB-010` Do not include attributes in the closing tag; they belong exclusively in the opening tag
  - Why: The parser ignores attributes on closing tags, so anything placed there silently does nothing and misleads the next reader.
- `WEB-011` Keep the <head> lean. Only include metadata, titles, and links to critical external resources (CSS/JS)
  - Why: Everything in the head is fetched or parsed before the page renders, so every extra tag or script there delays first paint.
- `WEB-012` Do not ever include more than one <body> tag, as this violates the structural integrity of the DOM
  - Why: The parser merges extra body tags into the first one, so their attributes and the intended structure are lost and the document is invalid.
- `WEB-013` Use exactly one visible <main> per document to wrap the primary content; on plain pages it is a direct child of <body>, and in framework apps it may sit inside the app root (e.g., <div id="root">), but it is never nested in <header>, <nav>, <footer>, <article>, or <aside> (see WEB-196)
  - Why: <main> is the landmark screen-reader users jump to; two visible ones, or one inside another landmark, make that jump target ambiguous. The app-root allowance exists because React and Vite render into a div.
- `WEB-025` Do use double quotes for attribute values as the primary convention
  - Why: Double quotes are the convention across HTML, JSX and tooling, and one consistent style avoids escaping mistakes when values contain apostrophes.
- `WEB-026` Do provide explicit attribute values (e.g., checked="checked") when the markup will be parsed as XML (XHTML, inline SVG served as XML, or markup embedded in XML documents)
  - Why: XML parsers reject attributes without values, so one bare boolean attribute stops the whole SVG or XHTML document from loading.
- `WEB-027` Do always include the lang attribute on the root <html> element
  - Why: Screen readers choose pronunciation from lang, and browsers use it for hyphenation, translation offers and font selection; without it they guess.
- `WEB-028` Don't use boolean-attribute shorthand (e.g., a bare checked) in markup that must also be valid XML (XHTML, SVG, XML templates); write the full attribute and value
  - Why: The shorthand is valid HTML but a well-formedness error in XML, which fails the entire document rather than just that attribute.
- `WEB-182` DO include <meta charset="UTF-8"> as the very first declaration inside the <head> tag to guarantee predictable text parsing before any content is read
  - Why: The browser must know the encoding before it reads any text; declared late or not at all, it may re-parse the page or show garbled characters.
- `WEB-183` DO include the responsive <meta name="viewport" content="width=device-width, initial-scale=1.0"> tag on every HTML document to ensure proper scaling on mobile screen viewports, and never disable zoom with user-scalable=no or maximum-scale=1
  - Why: Without it mobile browsers render a ~980px desktop page and shrink it; disabling zoom fails WCAG 1.4.4 and locks out low-vision users.
- `WEB-186` DO maintain strict numerical progression for heading levels (<h1> -> <h2> -> <h3>)
  - Why: Screen-reader users navigate by heading level; a skipped level makes them think content is missing and breaks the document outline.
- `WEB-189` DON'T include more than one <h1> on a single document; HTML technically allows several, but a single <h1> is the accepted convention for a clear page outline
  - Why: One h1 gives search engines and assistive technology an unambiguous page topic; several compete for that role.
- `WEB-190` DON'T place sensitive operational remarks or internal business logic notes inside public HTML comment blocks
  - Why: HTML comments ship to every visitor and show in View Source, so internal notes leak to competitors and attackers.
- `WEB-193` DO organize every page layout using semantic region containers (<header>, <main>, <footer>)
  - Why: These landmarks let assistive-technology users jump straight to the region they want and give every page a predictable structure.
- `WEB-195` DO apply aria-label or aria-labelledby attributes to distinguish individual navigation blocks when deploying multiple <nav> regions, using short labels such as "Main" or "Footer" without the word "navigation", since the role is already announced
  - Why: With several nav landmarks a screen reader lists "navigation, navigation"; a label tells them apart, and "navigation" inside it would be announced twice.
- `WEB-196` DON'T nest the <main> structural container inside <header>, <nav>, <footer>, <article>, or <aside> tags
  - Why: Nested that way, the primary content looks like part of a header or sidebar to assistive technology, and the document is invalid.

## Semantics and containers

- `WEB-014` Do not fall victim to "Div-itis": don't use <div> or <span> when a more descriptive element such as <nav>, <article>, <section>, or <aside> exists, and don't use an inline <span> where a block-level container is required
  - Why: Semantic elements give screen readers landmarks and search engines meaning for free; a page of divs and spans conveys nothing without extra ARIA.
- `WEB-041` DO use <b> for text segments where boldface is the standard convention but no additional semantic weight is required
  - Why: <b> marks stylistic offset (keywords, product names) without claiming importance, which keeps <strong> meaningful for real emphasis.
- `WEB-042` DON'T use <b> or <em> for titles or headings; utilize the established <h1> through <h6> hierarchy to maintain document structure
  - Why: Headings build the outline that screen readers and search engines navigate; bold or emphasized text is invisible to that outline.
- `WEB-043` DO use <br> in specific contexts like addresses where the line break is an inherent part of the data's structural meaning
  - Why: In an address or a poem the line break is part of the content itself, so it belongs in the markup rather than in CSS.
- `WEB-044` DON'T use <br> to create visual space between paragraphs; utilize <p> elements and CSS margin to ensure proper accessibility for screen readers, which may otherwise announce "blank" for repeated breaks
  - Why: Repeated breaks are announced as "blank" and give spacing that cannot change per breakpoint; paragraph margins can.
- `WEB-046` DO use <div> for grouping content specifically for layout purposes (e.g., Grid/Flexbox)
  - Why: A div carries no meaning, which is exactly right when the grouping exists only for layout.
- `WEB-047` DO use <span> for inline-level styling of specific phrasing content
  - Why: A span carries no meaning, so it styles part of a sentence without implying emphasis or importance.
- `WEB-051` DON'T use the obsolete align attribute; replace it with modern CSS Flexbox or Grid
  - Why: align is obsolete in HTML5 and cannot respond to screen size; Flexbox and Grid can, and they keep layout in the stylesheet.
- `WEB-052` DON'T expect generic containers to have any visual effect or layout presence without CSS
  - Why: div and span have no default styling beyond display type, so expecting spacing or layout from them alone leads to "why doesn't this work" bugs.
- `WEB-053` DON'T nest a <div> inside a paragraph or other elements that only permit phrasing content
  - Why: The parser closes the <p> as soon as it meets the <div>, splitting the paragraph and leaving an empty one behind, which breaks styling and scripts.
- `WEB-187` DO use semantic tags (<strong>, <em>) over purely visual tags (<b>, <i>) when emphasis or importance is intended, so the meaning lives in the markup and not only in the appearance
  - Why: strong and em carry importance and stress to screen readers and search engines; b and i only change appearance.
- `WEB-188` DO use HTML entities (&lt;, &gt;) whenever displaying literal markup code samples within body text blocks
  - Why: Raw < and > are parsed as tags, so code samples vanish or break the page; entities render them as text.

## Classes, IDs and data attributes

- `WEB-048` DO use classes for styling, recurring styles, and shared behaviors, and unique IDs for JavaScript manipulation, to prevent code confusion; avoid ID selectors in CSS because their high specificity is hard to override
  - Why: Classes are reusable and low-specificity, so styles stay easy to override; IDs are unique handles, so scripts targeting them cannot hit the wrong element.
- `WEB-054` DO ensure 100% uniqueness of every id within the document; reusing an id breaks document validity and causes fragment collision and script failure
  - Why: With duplicate ids, getElementById, label for= and ARIA references silently pick the first match, and #fragment links jump to the wrong place.
- `WEB-055` DO use consistent naming schemes (camelCase, dash-case, or snake_case) starting with a letter
  - Why: A consistent scheme keeps selectors predictable, and a leading digit forces escaping in CSS selectors.
- `WEB-057` DON'T rely on window.id for element selection
  - Why: Elements with an id appear as global window properties, but any global variable with the same name shadows them, so the lookup breaks silently.
- `WEB-059` DO separate multiple class names with standard ASCII whitespace
  - Why: The class attribute is split on ASCII whitespace only; commas or other separators become part of one invalid class name.
- `WEB-060` DON'T use presentational names that lose meaning when the UI is redesigned
  - Why: Names like .red-text or .left-col become lies after a redesign; names that describe purpose, like .error-message, survive it.
- `WEB-061` DO use data-* for internal script data, UI state syncing, and non-visual metadata
  - Why: data-* is the standard, valid place for script data, readable through dataset, instead of inventing invalid attributes.
- `WEB-062` DON'T store critical user-facing content in data attributes
  - Why: Data attributes are not exposed to assistive technology or search engines, so content stored there is invisible to them.
- `WEB-063` DON'T use data-* for styling if a standard class or state-based attribute is more appropriate
  - Why: A class or a standard state attribute (aria-expanded, disabled, :checked) already carries the meaning; a parallel data attribute duplicates state that can drift.

## Links

- `WEB-015` Use descriptive, contextual link text (e.g., "View Technical Specs") that describes the destination, rather than "Click Here" or a pasted raw URL, to improve accessibility and SEO
  - Why: Screen-reader users often browse a list of links out of context, where "Click here" means nothing; descriptive text also tells search engines what the target is about.
- `WEB-016` Do not omit the protocol in absolute links, or the browser will incorrectly attempt to find the resource as a relative path
  - Why: Without https:// the browser treats example.com as a path on your own site, and the link returns 404.
- `WEB-035` DO use the href attribute to create a hyperlink to addressable URLs to ensure the link is functional and focusable
  - Why: Without href an <a> is not focusable or announced as a link, so keyboard and screen-reader users cannot use it.
- `WEB-036` DON'T use the <a> element without an href unless it is intended as a placeholder or a "generic" link (per implicit ARIA roles)
  - Why: An <a> without href has no link role and no keyboard access, so using it for real links or actions leaves them unreachable.
- `WEB-037` DO set target="_blank" for external links to maintain session continuity, noting that modern browsers implicitly provide rel="noopener" behavior for such links
  - Why: It keeps the user's place on your site while they read the external page; WEB-039 makes sure the new window is announced.
- `WEB-038` DON'T rely on the download attribute for cross-origin URLs, as security policies will typically cause the browser to ignore the attribute and navigate normally
  - Why: Browsers ignore download on cross-origin URLs, so users navigate away instead of getting the file; serve it same-origin or with Content-Disposition: attachment.
- `WEB-039` DO provide clear alt text for any icons within links to ensure the intended behavior (e.g., "opens in new window") is announced to screen readers
  - Why: An icon alone says nothing to a screen reader, so users are surprised by a new window or a file download.
- `WEB-040` DON'T use <a> elements for non-navigation actions; the <button> element is the semantically correct choice for trigger-based interactions
  - Why: Buttons get Enter and Space activation, the right role and form behavior for free; an action dressed as a link misleads screen readers and breaks middle-click.
- `WEB-191` DO use relative URLs for internal file navigation to keep projects portable across local test servers and live domains
  - Why: Relative URLs keep working when the site moves between localhost, staging and production; absolute internal URLs break or point at the wrong environment.
- `WEB-192` DON'T expose raw personal email addresses directly in plain text or mailto: links on public websites without a mitigation (a contact form or address obfuscation), since search engine web crawlers scrape these links for bulk spam distribution lists
  - Why: Harvesting bots collect plain addresses quickly, and once collected the address receives spam permanently.

## Lists

- `WEB-064` DO use <dl> for associative metadata and glossaries to preserve key-value semantics
  - Why: dl tells assistive technology which term belongs to which description, which styled lists or divs cannot express.
- `WEB-065` DO utilize <div> wrappers inside <dl> for styling groups as per the WHATWG HTML Living Standard
  - Why: One div around each term/description group is the only valid way to style a pair as a unit.
- `WEB-066` DON'T use <dl> merely to achieve visual indentation; use CSS margin instead
  - Why: Screen readers announce a definition list and its items, so using one only for indentation describes a structure that is not there.
- `WEB-067` DON'T apply ARIA term or definition roles without comprehensive testing, as this may disrupt VoiceOver announcements
  - Why: Support for these roles is inconsistent, and on VoiceOver they can make content be skipped or announced wrongly.
- `WEB-068` DO ensure every <li> is strictly contained within a valid <ol>, <ul>, or <menu>
  - Why: An li outside a list is invalid, and screen readers then cannot announce the list size or the item's position.
- `WEB-069` DO use the value attribute when a specific sequence break is required in an ordered list
  - Why: value sets one item's number, so numbering stays correct when a list is split or resumes after an interruption.
- `WEB-070` DON'T use the type attribute on <ul> or <li>, and prefer CSS list-style-type for numbering styles; use type on <ol> only when the numbering style carries meaning (e.g., legal clauses)
  - Why: type on ul and li is obsolete and presentation belongs in CSS; on ol it is kept for when the marker is part of the meaning, as when text refers to "clause b".
- `WEB-071` DON'T use <li> for visual bulleting without a semantic container
  - Why: Bullets without a list container lose the "list, 5 items" announcement and fail validation.
- `WEB-072` DO apply the reversed attribute for descending rankings or countdowns
  - Why: reversed makes the numbering count down by itself, so it stays correct when items are added, with no hardcoded numbers.
- `WEB-073` DO implement CSS counters for complex or nested numbering needs that require custom logic beyond standard list behavior
  - Why: Counters produce nested or custom numbering (1.2.3) without hardcoded numbers that go stale when items move.
- `WEB-074` DON'T rely on the compact attribute; utilize modern CSS for visual density
  - Why: compact is obsolete and ignored by modern browsers, so it has no effect.
- `WEB-202` DO nest child sub-lists directly inside parent <li> items when creating nested list structures
  - Why: A sub-list placed directly in another <ul> or <ol> is invalid; inside the parent <li> it tells screen readers which item it belongs to.

## Tables

- `WEB-075` DO use tables exclusively for tabular data where a logical relationship exists between rows and columns
  - Why: Table semantics let screen readers announce the row and column headers for every cell, which is exactly what tabular data needs.
- `WEB-076` DON'T use tables for webpage layout; this violates semantic standards and hinders accessibility
  - Why: Layout tables are read out as data with nonsense headers and cannot reflow on small screens; CSS Grid does layout properly.
- `WEB-077` DO wrap column category headers in <thead> to provide a clear entry point for data parsing, and wrap the data rows in <tbody> on complex production tables
  - Why: thead and tbody separate headers from data for assistive technology and scripts, repeat headers on printed pages, and give clean styling hooks.
- `WEB-078` DO use <tfoot> for terminal data like "Total Balance" or "Grand Totals."
  - Why: tfoot marks summary rows as summaries, so they are not read as one more data row.
- `WEB-079` DON'T place <thead> anywhere other than its designated position in the sequence; modern standards prioritize a Caption -> Colgroup -> Thead -> Tbody -> Tfoot order
  - Why: Parsers and assistive technology expect this order; sections out of order render unpredictably and fail validation.
- `WEB-080` DO place the <caption> tag immediately after the opening <table> tag
  - Why: The spec requires caption to be the table's first child; anywhere else it is invalid and may not be tied to the table.
- `WEB-081` DON'T use the deprecated summary attribute; all descriptive metadata should be handled via <caption> or modern ARIA attributes
  - Why: summary is obsolete and ignored by modern assistive technology, so the description never reaches anyone.
- `WEB-082` DO carefully calculate cell counts in subsequent rows to account for "trimmed" slots created by vertical spans
  - Why: A rowspan cell occupies slots in the rows below; forgetting to drop cells there pushes those rows out of alignment.
- `WEB-083` DON'T overcomplicate spans to the point where the structure becomes unreadable; if a table cannot be parsed logically, it often indicates the data should be broken into smaller, related tables
  - Why: Complex spans are hard for assistive technology to announce and hard for anyone to maintain; splitting the data usually clarifies it.
- `WEB-084` DO supply a clear <caption> to help users decide if the table content is relevant to their needs
  - Why: The caption is the table's accessible name, letting screen-reader users decide from the list of tables whether to read one.
- `WEB-085` DO use the scope attribute (scope="col" and scope="row") explicitly on <th> cells so screen readers navigate grid coordinates accurately, and always in any table utilizing spans to ensure AT integrity
  - Why: scope states whether a header labels a column or a row; without it screen readers guess, and with spans they often guess wrong.
- `WEB-086` DON'T rely on visual-only cues like bolding or background colors to indicate header-data relationships
  - Why: Visual cues are not exposed to assistive technology; only th and scope create the header-data relationship.
- `WEB-087` DO use text-align: right for currency and numerical values to facilitate easy visual comparison
  - Why: Right-aligned numbers line up by place value, so magnitudes can be compared at a glance.
- `WEB-088` DO use vertical-align: bottom for headers spanning multiple rows to maintain alignment with the data
  - Why: A tall header aligned to the bottom sits next to the data it labels instead of floating above it.
- `WEB-089` DON'T use the non-standard height attribute on <table> or its cells; utilize min-height in CSS for layout control (this does not apply to the width and height attributes on <img>, which help prevent layout shift)
  - Why: height is not a valid table attribute; min-height in CSS lets rows grow with their content instead of clipping it.

## Images, media and embeds

- `WEB-018` Provide meaningful alt text that describes the actual content of the image, and never rely on an image alone to convey critical information; avoid filler text such as alt="image" or alt="picture" (decorative images: see WEB-200)
  - Why: alt is what screen readers announce and what appears when the image fails to load; filler text says nothing, and information carried only by the image is lost.
- `WEB-090` DO use nested <source> elements (inside <picture>, <video>, or <audio>) with explicit type attributes to prevent the browser from downloading unsupported formats
  - Why: With a type the browser skips formats it cannot play without downloading them, and picks the first supported source.
- `WEB-091` DO provide a direct download link as fallback content inside <audio> and <video> for accessibility and legacy support
  - Why: Browsers that cannot play the media show the fallback, so the user can still get the file.
- `WEB-092` DON'T use autoplay without a user-controlled opt-in; it is a major friction point for user experience
  - Why: Unexpected sound startles users and talks over screen readers, and browsers block unmuted autoplay anyway.
- `WEB-093` DON'T expect loading="lazy" to work on <audio> or <video>; it only applies to <img> and <iframe>, so use preload="none" (or preload="metadata") to defer media loading
  - Why: loading="lazy" is ignored on media elements, so it saves nothing; preload is the real control over what is fetched before playback.
- `WEB-094` DO place the <figcaption> as the first or last child within the <figure>
  - Why: Only as the first or last child is a figcaption treated as the figure's caption.
- `WEB-095` DO reserve <figure> for truly self-contained units; DON'T wrap every image in a figure if it is purely decorative or integral to the sentence
  - Why: figure means content that could move elsewhere and still make sense; wrapping decorative or in-sentence images adds noise for assistive technology.
- `WEB-096` DON'T use more than one <figcaption> per <figure>; a figure allows only a single caption as its official label
  - Why: The spec allows one figcaption per figure; extra ones are invalid and only one is used as the label.
- `WEB-097` DO always include a title attribute on <iframe> to prevent context-shift confusion for screen reader users
  - Why: The title is the frame's accessible name; without it screen readers announce just "frame", with no hint of what is inside.
- `WEB-098` DO use loading="lazy" on <iframe> to improve initial page load times for off-screen frames
  - Why: Embeds such as maps and videos are heavy; lazy loading defers them until the user scrolls near.
- `WEB-099` DON'T use deprecated attributes like frameborder or scrolling on <iframe>; manage these via CSS
  - Why: Both are obsolete; CSS border and overflow do the same job and keep styling in the stylesheet.
- `WEB-100` DON'T expect error events from <iframe> for security reasons; load events fire even if the content fails, preventing local network probing
  - Why: Browsers deliberately hide iframe load failures so pages cannot probe the local network, so an error handler never fires; check the outcome another way.
- `WEB-198` DO define explicit width and height dimensions on images to reserve space and reduce Cumulative Layout Shift (CLS), and pair them with CSS such as max-width: 100%; height: auto for responsive layouts
  - Why: The dimensions let the browser reserve space before the image arrives, so content does not jump; the CSS keeps the image responsive.
- `WEB-199` DO apply loading="lazy" to images positioned below the visual scroll fold to improve initial page load speeds, and never to above-the-fold or main (LCP) images; give the main image fetchpriority="high" instead
  - Why: Lazy loading below the fold saves bandwidth, but on the main image it delays Largest Contentful Paint; fetchpriority makes that image load first.
- `WEB-200` DO use an empty alt="" on purely decorative images so screen readers skip them
  - Why: An empty alt tells screen readers to skip the image; a missing alt makes many of them read the file name instead.
- `WEB-201` DON'T rely on <iframe> tags to display content from external domains without verifying that the target domain permits cross-origin framing (X-Frame-Options / CSP frame-ancestors), and use the sandbox attribute for untrusted embeds
  - Why: Sites that forbid framing show a blank or error box, and sandbox stops an untrusted embed from running scripts, submitting forms or navigating your page.

## Forms

- `WEB-102` DO assign unique name attributes to forms to ensure they are correctly referenced in the document.forms collection
  - Why: A name lets scripts reach the form as document.forms.name instead of a fragile index that changes when forms are added.
- `WEB-103` DON'T nest a <form> inside another <form>; this is prohibited content and will lead to unpredictable submission behavior
  - Why: The parser drops the inner form tag, so its fields silently submit with the outer form.
- `WEB-104` DON'T use the deprecated accept attribute on the <form> tag; modern standards require this to be placed directly on the <input type="file">
  - Why: accept on form is obsolete and ignored; browsers only read it on the file input.
- `WEB-105` DO use semantic type values (e.g., email) to trigger the correct virtual keyboards and built-in validation
  - Why: Phones show the matching keyboard (@ for email, digits for tel), and the browser checks the format before submit.
- `WEB-106` DO use the for attribute on <label> elements to explicitly associate them with the id of an input, enhancing accessibility
  - Why: The association gives the input its accessible name and makes the label clickable, which enlarges the target.
- `WEB-107` DON'T rely exclusively on client-side validation; while attributes like required aid the UI, all data must be verified server-side
  - Why: Anyone can bypass client-side checks with devtools or a direct request; only the server can protect the data.
- `WEB-108` DO monitor the change event to process files immediately after selection
  - Why: Reacting on change gives instant feedback (preview, size check) instead of surprising the user at submit time.
- `WEB-109` DO handle the cancel event to manage interactions where the picker is closed without a selection
  - Why: Without it the interface can stay stuck in a "waiting for a file" state after the user closes the picker.
- `WEB-110` DON'T assume the accept attribute provides absolute validation; it is a UI hint that users can often override in the file dialog
  - Why: Users can switch the dialog to "All files", so the type must still be checked in code and on the server.
- `WEB-111` DO provide clear feedback messages if no files are selected or if an invalid file type is chosen
  - Why: A silent failure leaves users unsure whether the upload worked; a clear message tells them what to fix.
- `WEB-112` DO ensure custom interfaces remain keyboard-accessible by using <label> elements to proxy clicks to hidden inputs
  - Why: A label tied to the real input forwards clicks and keeps keyboard focus working, so a custom-styled control stays usable.
- `WEB-113` DON'T use visibility: hidden or display: none for custom-styled inputs, as they remove the element from the tab order; use a visually-hidden technique instead
  - Why: Those properties remove the input from the tab order and the accessibility tree, so keyboard and screen-reader users cannot reach it.
- `WEB-203` DO define shared name attributes across radio button groups to ensure mutually exclusive single-option selection
  - Why: Radios sharing a name form one group: only one can be selected, and the arrow keys move within it.
- `WEB-204` DO include name attributes on every submit-ready input control; omitting name prevents data submission to processing endpoints
  - Why: Only named fields are included in the submitted data, so a missing name silently drops the value.
- `WEB-205` DON'T use method="GET" to transmit sensitive user passwords, credit card numbers, or confidential form payloads; use method="POST" instead
  - Why: GET puts the data in the URL, which is stored in browser history, server logs, proxies and Referer headers.
- `WEB-206` DON'T rely on placeholder text as a visual replacement for formal structural <label> elements
  - Why: A placeholder disappears as soon as the user types, usually has low contrast, and is not a reliable accessible name.
- `WEB-207` DON'T place the autofocus attribute on multiple inputs within a single HTML document
  - Why: Only one element can take focus on load, and unexpected focus moves disorient screen-reader users; several autofocus attributes make it unpredictable.

## Text-level semantics

- `WEB-114` DO use <abbr> and expand terms in plain text on first use to ensure cognitive accessibility
  - Why: Writing the expansion out helps every reader, including those who cannot hover to see a tooltip.
- `WEB-115` DO maintain grammatical number symmetry between the expansion (title) and the inner text of <abbr>
  - Why: If the text is plural ("APIs") the expansion must be too, or screen readers that read the title produce a mismatched sentence.
- `WEB-116` DON'T use the title attribute on <abbr> if the expansion is already present in the surrounding text flow
  - Why: The title would only repeat the expansion, and some screen readers would read it twice.
- `WEB-117` DON'T rely on the title attribute as a primary source of information, as tooltips are often inaccessible to non-pointer users
  - Why: Title tooltips need a mouse hover, so touch, keyboard and many screen-reader users never see them.
- `WEB-118` DO use <cite> exclusively for the title of a work or its abbreviated form
  - Why: cite means the title of a work; using it for other things weakens that meaning for assistive technology and parsers.
- `WEB-119` DO apply CSS to normalize font styles if the default italics of <cite> are not desired
  - Why: The italics are only default presentation; CSS changes them without losing the meaning.
- `WEB-120` DON'T use <cite> to mark up the names of people or authors (unless the name is part of the title)
  - Why: The spec defines cite for titles of works, not people.
- `WEB-121` DON'T use the <cite> element when you intend to provide a quote source URL; use the cite attribute on <q> or <blockquote> instead
  - Why: The element is visible text naming a work; the attribute holds a machine-readable source URL for the quotation.
- `WEB-122` DO reserve <article> for content that is "independently distributable" (e.g., in a feed or RSS)
  - Why: article marks a unit that makes sense on its own, so feeds and reading modes can extract it whole.
- `WEB-123` DO use nested <article> tags to indicate comments related to a primary post
  - Why: Nesting tells assistive technology and parsers that the comments belong to that post.
- `WEB-124` DON'T place an <article> inside an <address> container
  - Why: address holds contact details for its nearest article or body; an article inside it inverts that relationship and is invalid.
- `WEB-125` DON'T use <article> for content fragments that lack internal logic or standalone value
  - Why: Overusing article fills the landmark list with fragments and hides the real articles among them.

## Files and local development

- `WEB-179` DO use lower-case characters, hyphens, or underscores for file names (e.g., index.html, about.html, lesson-01.html), and never spaces or uppercase letters, because Linux/Unix web servers treat paths as case-sensitive, leading to broken links (404 Not Found)
  - Why: A case mismatch works on Windows and macOS but 404s on a Linux server, and spaces turn into %20 in every URL.
- `WEB-180` DO name your site's primary landing page index.html, as web servers automatically look for this default file name when resolving domain root requests
  - Why: Servers serve index.html for a directory request by default, so the site loads at the bare domain with no extra configuration.
- `WEB-181` DON'T open HTML files purely via the file:// protocol during development; always launch via a local HTTP development server (e.g., Live Server) to mimic production network conditions
  - Why: file:// breaks fetch, ES modules, CORS, cookies and root-relative paths, so a page can work locally and fail in production, or the reverse.

## Validation

- `WEB-020` Validate your markup frequently, and run every HTML document through validator.w3.org before it goes to production. A single misplaced symbol can break a layout, so do not ignore validator warnings even if the page looks fine in your browser
  - Why: Each browser silently repairs invalid markup in its own way, so the bug surfaces later in another browser or screen reader; the validator shows it now.

## Merged rules

WEB-049 and WEB-101 → WEB-009 · WEB-050 and WEB-197 → WEB-014 · WEB-056 → WEB-054 ·
WEB-058 → WEB-048 · WEB-167 → WEB-018 · WEB-194 → WEB-013 · WEB-126 and WEB-127 → WEB-001

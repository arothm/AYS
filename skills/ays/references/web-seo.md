# Web — SEO

Load when building or reviewing public pages that should rank in search or be
cited by AI answers: content, metadata, structured data, indexing. Each rule's
"Why" is the reason to follow it; use it to judge cases the rule does not spell
out.

## Indexing

- `WEB-157` DO use the URL Inspection Tool in Search Console to see exactly how Googlebot renders your page
  - Why: It shows the page as Googlebot renders it, including blocked resources and script errors you never see in your own browser.
- `WEB-158` DO ensure that your sitemap is submitted and updated to reflect new content
  - Why: A current sitemap tells search engines which pages exist and when they changed, so new content is found sooner.
- `WEB-159` DON'T block crawlers from accessing assets that are required for the page's visual or functional integrity
  - Why: If Googlebot cannot load your CSS or JavaScript, it cannot render the page as users see it and may rank it lower.
- `WEB-160` DON'T assume a live page is an indexed page; always verify via Search Console
  - Why: A page can be live yet excluded (noindex, duplicate, crawl error), and only Search Console shows whether it is indexed.

## Content

- `WEB-161` DO write for humans first; the algorithm is designed to follow the user
  - Why: Ranking systems reward pages that satisfy readers; text written for algorithms reads badly and ages poorly.
- `WEB-162` DO update or prune "zombie content" to maintain site-wide authority
  - Why: Outdated or thin pages lower the perceived quality of the whole site and waste crawl budget.
- `WEB-163` DON'T engage in keyword stuffing; it is a legacy tactic that violates Google's spam policies and hurts readability
  - Why: It is treated as spam and can get pages demoted, and it makes the text worse for readers.
- `WEB-164` DON'T copy content; unique, first-hand insights are the best way to stand out and earn trust from search engines
  - Why: Duplicate content adds nothing, so search engines filter it out; first-hand experience is what quality guidelines reward.
- `WEB-165` DO use original images; generic stock photos offer zero unique value
  - Why: Stock photos appear on thousands of sites, while original images can rank in image search and show real experience.

## Media

- `WEB-017` Use descriptive, lowercase, hyphenated filenames for media and images (e.g., primary-architecture-diagram.webp, organic-cotton-tshirt-blue.jpg), never generic ones like image1.jpg, to assist search engines in indexing your assets
  - Why: The file name is one of the signals image search uses to understand an image; a generic name gives it nothing.

## Metadata and structured data

- `WEB-184` DO keep meta descriptions concise (roughly 150-160 characters), since search engines may truncate longer ones in search snippets
  - Why: Longer descriptions are cut off in results, often mid-sentence, and lose their message.
- `WEB-185` DON'T use the meta keywords tag; major search engines ignore it, and stuffing it with irrelevant terms is a spam signal
  - Why: It brings no ranking benefit and only reveals your keyword strategy to competitors.
- `WEB-169` DO use Schema markup (e.g., Article, Product, Organization, and VideoObject with timestamps and key moments) to make your content machine-readable, only for content visible on the page and only for types Google currently supports, since its list of supported structured data features keeps changing; DON'T add FAQ markup expecting rich results, since Google stopped showing FAQ rich results on May 7, 2026
  - Why: Structured data makes pages eligible for rich results; markup for hidden content breaks Google's guidelines, and unsupported types are simply ignored.

## AI search

- `WEB-170` DON'T ignore SEO basics; strong organic rankings correlate with being cited in AI-generated answers
  - Why: AI answers draw heavily on pages that already rank, so the basics also decide whether AI cites you.
- `WEB-171` DON'T assume AI will "understand" your brand; you must explicitly define it
  - Why: Models can only repeat what they find stated clearly and consistently; vague brand information gets guessed or confused with others.

## Merged rules

WEB-166 → WEB-169 · WEB-168 → WEB-017

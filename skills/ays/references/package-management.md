# Package management

Load only when the project uses npm or pnpm (a package.json, package-lock.json
or pnpm-lock.yaml is present), or when about to install any package. Each rule's
"Why" is the reason to follow it; use it to judge cases the rule does not spell
out.

- `PKG-001` DO keep package.json strictly valid JSON (no comments, trailing commas, or single quotes), because tools and CI parse it as strict JSON
  - Why: One comment or trailing comma makes the file unparseable, and every install and CI run fails.
- `PKG-002` DO separate runtime dependencies (dependencies) from build-time and development tooling such as bundlers, compilers, and linters (devDependencies), and install with dev dependencies omitted in production, to keep the deployed footprint small
  - Why: Production installs then skip the build tools, so deploys are smaller, faster and carry fewer packages that could be vulnerable.
- `PKG-003` DON'T edit lockfiles by hand; change package.json and let the package manager regenerate the lockfile
  - Why: The lockfile holds integrity hashes and a resolved tree; hand edits break them and make installs inconsistent.
- `PKG-004` DON'T import packages that are not declared in package.json (transitive dependencies); declare every direct import explicitly
  - Why: An undeclared import only works because another package happens to bring it in, and breaks when that package updates or under pnpm's strict layout.
- `PKG-005` DON'T mix package managers in one repository (e.g., running npm install in a pnpm project); use the one indicated by the lockfile or the packageManager field
  - Why: Each manager has its own lockfile and layout, so mixing them creates conflicting lockfiles and different dependency trees.
- `PKG-006` DO set a minimum release age so brand-new package versions are not installed immediately, as a guard against supply-chain attacks (npm: min-release-age in days, npm 11.10+, off by default; pnpm: minimumReleaseAge in minutes, pnpm 10.16+, on by default from pnpm 11; Bun: [install] minimumReleaseAge in seconds); units differ, so check them
  - Why: Malicious versions are usually caught and removed within days, so waiting means you almost never install one.
- `PKG-007` DO set an explicit store-dir (or use a cache mount) in pnpm Docker builds so the store is on the same filesystem as node_modules, because hard links cannot cross filesystems and pnpm then falls back to slower copying
  - Why: With the store on another filesystem pnpm copies every file instead of linking it, and installs become much slower.
- `PKG-008` DON'T force a flat node_modules layout in pnpm (e.g., node-linker=hoisted) unless a legacy native build tool cannot resolve symlinks
  - Why: pnpm's symlinked layout is what blocks undeclared imports (PKG-004); hoisting gives that protection up.
- `PKG-009` DO verify any package you are about to install (exact name, publisher, age, download history, linked repository) on the public registry (npm, PyPI), especially when an AI assistant suggested it, because hallucinated package names are a known attack vector (slopsquatting/typosquatting)
  - Why: Attackers register the names AI tools tend to invent and names one typo away from popular packages, and installing one runs their code.

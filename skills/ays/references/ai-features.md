# AI-powered features

Load only when building features that call LLMs or ML models, including agents,
RAG, tool calling, prompts, evals, or model pipelines. Each rule's "Why" is the
reason to follow it; use it to judge cases the rule does not spell out.

## Where a model belongs

- `AIF-001` DON'T ship opaque, probabilistic AI models for decisions in regulated domains (healthcare, financial risk scoring, automated compliance) without explainability, audit logging, and human review, because unexplainable outputs create compliance and liability risk
  - Why: Regulators and the people affected must be able to see why a decision was made, and an output nobody can explain cannot be justified or appealed.
- `AIF-003` DO implement fixed business logic, mathematical calculations, and explicit regulatory rules in ordinary deterministic code instead of a model, because they must be exactly reproducible and auditable, and keep multi-step deterministic workflows (e.g., static RAG pipelines or scripted API chains) as plain code with a clear boundary, using an agent only for steps that need adaptive reasoning
  - Why: A model can answer differently each time, while rules and calculations must give the same result every time and be auditable.
- `AIF-023` DO use the simplest approach that meets the requirement (a plain script or fixed workflow, then a single model call, then a tool-using agent, then multi-agent), prefer one agent that loads skills on demand over adding more specialized agents when a new domain appears, and don't use learning or utility-based agents for static, fully observable, single-condition tasks
  - Why: Each step up adds cost, latency and new ways to fail, and most tasks do not need the higher steps.
- `AIF-005` DO choose model size, latency, and reasoning effort to match the task: small, fast models for simple or high-volume work such as classification, data conversion, inline completion or boilerplate (e.g., Haiku 5.5 rather than Opus or Fable), larger or high-reasoning models for hard analysis, and large-context models only for full-codebase work; at volume, route each request by its complexity, length and risk to the cheapest model that passes your evaluations, and use a balanced mid-tier model (e.g., Sonnet 5.5, as of November 2026) as the default until evaluations say otherwise
  - Why: A large model on a simple task wastes money and time, and a small one on a hard task gives poor answers; at volume, routing each request to the cheapest model that passes saves the most.
- `AIF-034` DO use a natively multimodal model when the input is images, audio, video or scanned documents and the task depends on visual or audio detail (layout, charts, tone); a separate OCR or transcription step loses that detail, but stays cheaper when plain text is enough
  - Why: Converting media to text first throws away layout, charts and tone, but when only the words matter the cheaper pipeline gives the same answer.
- `AIF-035` DO choose models and AI platforms by scoring candidates against your own requirements (accuracy on your domain data, latency, cost, data terms, compliance) in a weighted decision matrix; use public leaderboards and benchmark averages only to shortlist, since they measure other tasks and may be contaminated by training data
  - Why: A model that tops a public benchmark can still fail on your data or terms, and only your own requirements show which one fits.
- `AIF-040` DO build AI features into the systems where the data and work already live (ERP, CRM, data warehouse) through their APIs, instead of standalone apps that copy data out and drift from the source of truth
  - Why: Copied data goes stale and multiplies the places it can leak, while a feature inside the existing system works on current data under its existing access controls.
- `AIF-041` DON'T assume a general model handles niche domain work out of the box: test it on your domain data first, then add context engineering and retrieval, and fine-tune only if evaluations still fall short
  - Why: General models often miss domain specifics, but fine-tuning is the most expensive fix, so cheaper steps should be proven insufficient first (see AIF-023).

## Output reliability

- `AIF-002` DON'T assume a model returns identical output for identical input; use low temperature (near 0) for extraction and structured-output tasks and avoid high temperature combined with unrestricted top-p where consistent schema adherence is required (where the model or API exposes these controls), state the exact JSON or XML output format in the prompt, use the provider's structured-output feature if available, and validate every response against a schema with fallback handling for malformed or hallucinated results, because temperature 0 alone does not guarantee valid output
  - Why: Even at temperature 0 a model can return malformed or different output, and schema validation catches it before it breaks your code.
- `AIF-016` DO, when building fill-in-the-middle completion features, apply stop tokens and trim any overlap between the generated text and the existing code after the cursor, to prevent duplicated code
  - Why: Models often regenerate the code that already follows the cursor, so without trimming the result is duplicated.

## Prompting

- `AIF-006` DO match the prompting technique to the task: zero-shot for simple classification; step-by-step reasoning (chain-of-thought prompting or the model's built-in reasoning mode) for multi-step math, logic, and structural reasoning; and avoid heavyweight search strategies such as Tree of Thoughts unless they are justified
  - Why: Reasoning steps add cost without helping simple tasks, complex ones fail without them, and heavy search strategies multiply cost.
- `AIF-012` DO structure prompts with explicit delimiters (e.g., XML-style tags such as <instructions>, <context>, <data>) and clear, direct instructions instead of conversational phrasing, so instructions stay separate from data; wrap user input and retrieved text in tags such as <user_input>, tell the model to treat the enclosed content as data, and never place unvalidated user input inside the system instructions (delimiters reduce prompt-injection risk but do not remove it)
  - Why: When instructions and data are mixed, injected text can pose as instructions; tags make the boundary explicit.
- `AIF-013` DO keep system prompts static and inject runtime values (names, customer identifiers, product variables) through template variables or structured data payloads instead of hardcoding them into the instructions, and take identity and permission values (user ID, tenant, roles) from the authenticated session, never from model-generated arguments
  - Why: A static prompt can be cached and versioned, and identity taken from model output can be forged through prompt injection.
- `AIF-014` DO state the desired output positively and add short explicit constraints where output tends to run long (e.g., "answer in one paragraph, no preamble"), rather than relying on a list of prohibitions
  - Why: Models follow a clear description of the wanted output more reliably than a list of things to avoid.
- `AIF-018` DO enable prompt caching for static content (system instructions, tool schemas, reference documents) and order prompts with that static content first and variable content last (user input, retrieved data) to maximize cache hits (cached input typically costs about a tenth of normal input), and don't resend large static documents or an excessive number of tool schemas on every call of a high-volume endpoint
  - Why: Providers cache identical prompt prefixes, so caching repeated content cuts input cost and latency, while variable content placed early breaks the cache on every call; the discount applies only to cached input, not to output or the rest of the bill.

## Context and retrieval

- `AIF-009` DO clean, truncate, and clearly delimit tool outputs before appending them to the model's context (e.g., convert raw HTML into structured Markdown or JSON summaries, and return only the fields the model needs), and treat them as untrusted data, never as instructions
  - Why: Raw tool output wastes tokens on noise and can carry injected instructions.
- `AIF-010` DO supply precise context through retrieval (RAG) or modular prompt sections instead of filling the context window, trim or summarize history before it nears the limit, and ground factual answers in retrieved sources rather than the model's memory alone; on critical paths, show inline citations to those sources and verify automatically that each claim is supported before the answer is used
  - Why: A stuffed context dilutes what matters and hits limits, while retrieved sources reduce made-up answers, and citations plus a support check catch the ones that remain before they cause harm.
- `AIF-011` DO count tokens before sending, using the provider's own tokenizer or token-counting API (e.g., tiktoken for OpenAI models), so requests do not hit the context limit or get truncated
  - Why: A request over the limit fails, or loses part of its input without warning.
- `AIF-015` DO validate dynamic context pipelines for null or missing database values, so placeholder text such as "{!Contact.FirstName}" or "null" never reaches the model
  - Why: Placeholders and nulls in a prompt produce nonsense answers that look like real ones.

## Tools and agents

- `AIF-007` DO use tool calling (the reason-act-observe pattern, e.g., ReAct) when the model must interact with external APIs, databases, or files
  - Why: Tools let the model act on real data instead of guessing at it.
- `AIF-008` DO cap turns, recursion depth, execution time, retries, max tokens, and spend on agent and self-reflection loops (e.g., Reflexion) to prevent runaway billing
  - Why: An agent loop can repeat indefinitely, and every turn costs money.
- `AIF-038` DO let current Claude models size their own reasoning with adaptive thinking and an effort setting (low, medium, high, xhigh, max) chosen per task, instead of fixed thinking-token budgets, which Opus 4.8 no longer accepts; cap total tokens, time and spend per task instead (see AIF-008)
  - Why: A fixed thinking budget is too small for hard steps and wasted on easy ones, and current models reject it; the per-task cap still bounds the cost.
- `AIF-017` DO define every tool with an explicit, typed parameter schema (JSON Schema) and use the model's native structured function calling instead of describing parameters in prose; validate each model-generated argument against the schema before executing any backend action, and return a clear error for missing or invalid parameters
  - Why: Model-generated arguments can be wrong or malicious, and schema validation stops them before they reach your backend.
- `AIF-024` DO plan the steps up front (plan-and-execute designs such as ReWOO) when token cost, latency, and predictability matter, and don't rely solely on open-ended ReAct loops for predictable tasks, because they can drift or loop (see AIF-008)
  - Why: A plan made up front uses fewer model calls and behaves predictably, while an open loop can wander.
- `AIF-025` DO structure multi-agent systems with a supervisor that delegates to agents with isolated, domain-specific responsibilities, giving low-level subtasks such as file parsing and data formatting to a small, fast model under a stronger orchestrator (e.g., Haiku 5.5 under Opus 5.5 or Sonnet 5.5, as of November 2026), and don't allow unmonitored peer-to-peer agent loops, which can cause cascading failures and exponential API consumption
  - Why: A supervisor keeps control and accountability in one place, while agents talking freely can amplify each other's errors and costs.
- `AIF-026` DO give every production agent a unique identifier, log its actions (inputs, tool calls, outputs, decisions) for audit, and provide a way to interrupt or disable it (kill switch)
  - Why: Without an identity and logs you cannot audit what an agent did, and without a kill switch you cannot stop it when it goes wrong.
- `AIF-027` DO keep the set of tools exposed to a single agent small and relevant, because every tool schema consumes context and many overlapping tools confuse tool selection (around ten is a common rule of thumb, not a hard limit)
  - Why: Every tool takes up context, and similar tools make the model pick the wrong one.

## Security

- `AIF-019` DON'T give LLM agents direct, unmonitored write access to production databases or critical external APIs, or unrestricted access to destructive operations (e.g., SQL DROP TABLE, exec()); require human-in-the-loop approval for high-impact or mutating actions, use least-privilege credentials, and keep humans in control of agents in high-risk domains such as financial trading or emergency triage
  - Why: One bad output or one successful injection can destroy data; human approval and least privilege limit the damage.
- `AIF-020` DO add independent input and output guardrails (e.g., a classifier or guardrail model plus pattern checks) to detect prompt-injection attempts, PII leaks, and toxic or unauthorized output, never relying on keyword blocklists or regex filters alone, and run recurring red-team tests against the endpoint using an established security framework
  - Why: Prompts alone cannot prevent injection or data leaks, and blocklists miss rephrased output, so independent checks and regular attack testing catch what gets through.
- `AIF-036` DO state domain-specific compliance constraints as explicit principles in the system prompt, and also enforce every hard constraint in code or an independent guardrail (see AIF-003, AIF-020), because a prompt guides the model but cannot guarantee its output
  - Why: Stated principles make compliant answers more likely, but only a deterministic check guarantees a constraint holds every time.
- `AIF-028` DO keep credentials and OAuth flows entirely out of the model's context: let the tool layer or a dedicated authentication proxy attach tokens server-side, so the model never sees, stores, or handles secrets
  - Why: Anything in the model's context can be leaked through its output or extracted by injection.

## Providers, data and compliance

- `AIF-029` DO send proprietary or customer data only to AI providers whose contract excludes it from model training and limits retention (zero data retention where the provider offers it), with the compliance attestations your data requires (e.g., a SOC 2 Type II report; a HIPAA business associate agreement for health data); confirm which endpoints and features the agreement covers, and keep it on file
  - Why: Data sent to a provider without these terms may be stored or used for training, and zero-retention agreements often exclude some features, so coverage has to be checked.
- `AIF-030` DO encrypt AI data at rest with AES-256, using customer-managed keys (CMEK) where you must control or revoke the keys, protect it in transit with TLS 1.2 or higher (see WEB-022), and pin processing and storage to the required region when data-residency rules apply, confirming that logs and backups stay in that region too
  - Why: Encryption limits the damage of a breach, your own keys let you revoke access, and residency is broken as soon as one copy, log or backup leaves the region.
- `AIF-031` DO reserve dedicated model capacity (e.g., Azure provisioned throughput units, Amazon Bedrock provisioned throughput, or private inference endpoints) when steady volume or a latency SLA justifies the fixed cost; stay on pay-per-use capacity for low or spiky traffic
  - Why: Shared capacity can slow down under other customers' load, but reserved capacity is billed whether used or not, so it only pays off at steady volume (compare OPS-004).
- `AIF-032` DO route production model traffic through a central gateway that writes tamper-evident, time-stamped logs of each call (caller, model, purpose, data classification), restricts access by role (RBAC), and forwards events to the security monitoring system (SIEM); log prompt and response content only where policy allows, with secrets and personal data redacted
  - Why: One gateway gives one place to audit, restrict and monitor every model call, and redaction keeps the logs from becoming a store of sensitive data (see AIF-026).
- `AIF-033` DON'T couple application code directly to one model vendor's API; call models through a thin internal interface or gateway, with circuit breakers that fail over to another provider or region when one errors or times out, and run your evaluations on each fallback model before it serves traffic (see AIF-022)
  - Why: A direct dependency turns a vendor outage or price change into your outage or rewrite, and an unevaluated fallback can behave differently from the model it replaces.
- `AIF-039` DON'T use restricted-access models (e.g., Claude Mythos 5, available only to vetted organizations through Project Glasswing) outside the gated environment and governance oversight their access agreement requires
  - Why: Access to these models is granted on conditions, and using them outside those conditions breaks the agreement and removes the oversight it requires.
- `AIF-042` DO check each region's AI and data rules (e.g., the EU AI Act, data-residency and export laws) before deploying a model feature there, and apply the stricter regional controls instead of bypassing them for a global rollout
  - Why: A feature that is legal in one country can be restricted in another, and bypassing local controls exposes the company to fines and forced withdrawal.

## Data and evaluation

- `AIF-004` DO split datasets into separate training, validation, and test sets before running a model pipeline (and before any preprocessing fitted on the data), to prevent data leakage so metrics reflect performance on unseen data
  - Why: Testing on data the model has already seen inflates the scores, and the model then disappoints on real data.
- `AIF-021` DO keep production prompts under version control and change them only after running a baseline regression suite; compare prompt variants against objective metrics (tools such as DSPy can automate this), evaluate agents by end-to-end task completion rate rather than output volume or speed, and give each skill or agent component its own isolated evaluation suite and production telemetry before deploying it
  - Why: A prompt change can break cases that used to work, and only regression tests and real metrics show it.
- `AIF-022` DO re-run your evaluations whenever you change models or model families (including from a proprietary model to an open-weights one), and don't assume a prompt tuned for one model performs equivalently on another
  - Why: The same prompt behaves differently on another model, and only re-evaluating shows what changed.
- `AIF-037` DO check high-volume model outputs automatically with a model-based grader (LLM-as-judge) against written criteria, and have people review a random sample plus every flagged output, because human review alone cannot keep up and an automated grader alone can share the model's blind spots
  - Why: Each method covers the other's weakness: the grader scales and the human sample catches what the grader misses.

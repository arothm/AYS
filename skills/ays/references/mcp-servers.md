# MCP servers

Load only when building or configuring MCP servers or clients. Each rule's "Why"
is the reason to follow it; use it to judge cases the rule does not spell out.

## Design

- `MCP-001` DO expose reusable tool capabilities through a modular MCP server built with the official SDK instead of proprietary, model-specific tool wrappers, so any compliant host (e.g., Claude Desktop, Cursor, VS Code) can use them
  - Why: One standard server works in every compliant host, instead of rebuilding the same tools for each model or app.
- `MCP-002` DON'T build an MCP server when a simple, declarative script packaged in a local Agent Skill can reach the same goal without protocol overhead
  - Why: A server is one more process, protocol and thing to maintain; a script in a skill is simpler when it does the job.
- `MCP-003` DON'T mix application UI state into tool execution logic; keep MCP servers modular and independent of any one transport
  - Why: UI state inside tool logic ties the server to one app and one transport, so it cannot be reused.
- `MCP-004` DO expose state-changing actions as Tools, never as read-only Resources
  - Why: Hosts may read resources automatically, so an action exposed as a resource can run without anyone intending it.
- `MCP-012` DO use MCP prompt templates for reusable, user-selectable prompts that should travel with the server, rather than as a replacement for the application's own prompts
  - Why: Templates give users ready-made workflows that ship with the server, but they do not replace the application's own logic.

## Tool handlers

- `MCP-005` DO define each tool's input schema once in code (e.g., a Zod schema) and derive both the TypeScript types and the JSON Schema inputSchema from it, validate all incoming arguments inside the tool-call handler, and throw typed protocol errors (e.g., McpError) for missing or invalid parameters
  - Why: One schema keeps types and validation from drifting apart, and typed errors tell the client exactly what was wrong.
- `MCP-006` DO catch exceptions inside tool handlers and return a short, readable error result that says what failed and what to try next, instead of returning raw stack traces to the model
  - Why: A stack trace wastes context and exposes internals, while a clear message lets the model correct course.

## Transport and security

- `MCP-007` DO use the stdio transport for local servers launched as child processes by the host; it has no network surface, and stdio servers take their credentials from environment variables instead of OAuth
  - Why: stdio is not on the network, so nothing outside the machine can reach the server.
- `MCP-008` DON'T expose a stdio server directly on network ports; anything reachable over a network needs a network transport with authentication and boundary access controls
  - Why: A stdio server has no authentication, so on an open port anyone who reaches it can use its tools.
- `MCP-009` DO run remote MCP servers over the Streamable HTTP transport (the older HTTP+SSE transport is deprecated), behind a reverse proxy with TLS, strict origin/CORS controls, and OAuth 2.1 authentication using narrowly scoped, least-privilege tokens
  - Why: The SSE transport is deprecated, and TLS, origin checks and narrowly scoped tokens stop unauthorized use.
- `MCP-010` DO route tool calls through interception middleware that enforces security policy and records audit logs, and never bypass it when carrying multi-tenant user contexts across shared remote servers
  - Why: Central middleware applies policy the same way every time and records who did what; bypassing it loses both.
- `MCP-011` DO configure server URLs through configuration or an approved registry and restrict clients to an allow-list of approved servers, instead of hardcoding URLs or auto-connecting to discovered ones
  - Why: Connecting to an unknown server lets it feed instructions to the model or collect your data.

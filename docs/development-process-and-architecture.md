# Development Process, Technology Stack, and Architecture

LaTeX version for report integration: `docs/development-process-and-architecture.tex`.

This document complements the implementation wiki and provides a structured view of:
- the end-to-end development process,
- the Agile Scrum methodology used during delivery,
- the current backend and UI architecture,
- and the Docker-based orchestration model.

It is written to be reused in reports where a section similar to "Technology Stack and Architecture" is required.

---

## 1. Technology Stack and Architecture

### 1.1 Backend Stack (mesx-proto-dependency-mgt-be)

- Runtime: Node.js
- Framework: NestJS (modular architecture)
- Language: TypeScript
- API style: REST + SSE (for task streaming)
- Validation and API docs: class-validator + Swagger
- External integration: Azure DevOps REST APIs (Work Item + Git)

### 1.2 UI Stack (mesx-proto-dependency-mgt-ui)

- Framework: Vue 3
- UI framework: Quasar
- Language: TypeScript
- Build tool: Vite
- HTTP client: Axios
- Streaming: EventSource (SSE consumption)

### 1.3 Container and Runtime Stack

- Containerization: Docker for backend and UI services
- Service packaging: separate Docker images per application
- Runtime config: environment variables and externalized configuration files
- Network model: UI calls backend over HTTP(S), backend calls Azure DevOps APIs

Figure placeholder:
- Figure 1 - Global technology stack and runtime topology
- Suggested file: docs/figures/tech-stack-topology.png

---

## 2. Development Methodology (Agile Scrum)

The project follows an Agile Scrum-inspired process adapted to a technical prototype context.

### 2.1 Scrum Roles (Adapted)

- Product Owner responsibility: define and prioritize traceability use cases.
- Scrum Master responsibility: keep sprint cadence, remove blockers, ensure process discipline.
- Development Team responsibility: implement backend, UI, contracts, tests, and documentation.

### 2.2 Sprint Structure

- Sprint Planning:
  - select user stories and technical tasks from prioritized backlog;
  - define sprint goal around one measurable traceability milestone.
- Daily follow-up:
  - track progress and blockers on backend/UI integration;
  - align API contracts and data mappings.
- Sprint Review:
  - demonstrate implemented trace scenarios (single root, batch flow, tag enrichment).
- Sprint Retrospective:
  - identify process, quality, and architecture improvements for the next sprint.

### 2.3 Agile Artifacts

- Product Backlog: functional and technical traceability items.
- Sprint Backlog: selected stories/tasks for current iteration.
- Increment: tested backend endpoints + usable UI flow + updated documentation.
- Definition of Done:
  - endpoint/UI behavior validated,
  - contract compatibility verified,
  - docs updated (wiki/spec/report sections),
  - regression risk reviewed.

Figure placeholder:
- Figure 2 - Scrum workflow used for implementation
- Suggested file: docs/figures/scrum-workflow.png

---

## 3. End-to-End Development Process

### 3.1 Process Phases

1. Requirement framing:
   - identify traceability pain points and target outcomes.
2. Architecture and contract design:
   - define module responsibilities and DTO contracts.
3. Backend implementation:
   - implement work item, pull request, and commit services.
4. UI implementation:
   - build route-based views, state handling, and API integration.
5. Integration and verification:
   - validate data flow from UI to backend to Azure DevOps and back.
6. Containerization and deployment preparation:
   - package services, configure runtime variables, and verify boot sequence.

### 3.2 Quality Gates Across Phases

- API contract checks between frontend models and backend DTOs.
- Functional checks for single and batch trace workflows.
- Error handling checks (auth redirection, API failures, partial data).
- Documentation updates after each major feature increment.

Figure placeholder:
- Figure 3 - End-to-end development lifecycle
- Suggested file: docs/figures/development-lifecycle.png

---

## 4. Architecture Detail - Backend

### 4.1 Backend Logical Structure

- Controller layer:
  - exposes `/workitem/*`, `/pullrequests/*`, `/commits/*` routes.
- Service layer:
  - orchestrates traversal, enrichment, and aggregation logic.
- Integration layer:
  - central Azure DevOps API access and normalization.
- DTO layer:
  - stable request/response contracts for UI consumption.

### 4.2 Main Backend Modules

- Work Item Module:
  - single related graph retrieval,
  - aggregated batch retrieval,
  - SSE task streaming.
- Pull Request Module:
  - linked work items by pull request,
  - pull request repository summary enrichment.
- Commit Module:
  - commits by work item and by pull request,
  - branch/tag resolution,
  - batch tag resolution.

Figure placeholder:
- Figure 4 - Backend module/component architecture
- Suggested file: docs/figures/backend-architecture.png

---

## 5. Architecture Detail - UI

### 5.1 UI Logical Structure

- Routing layer:
  - route entry points for single trace and batch trace screens.
- View layer:
  - graph and result pages for trace workflows.
- State/composable layer:
  - shared trace state, async orchestration, and SSE lifecycle handling.
- API layer:
  - typed backend adapters and auth-aware axios client logic.

### 5.2 Main Trace Flows

- Single flow:
  - one root work item -> `/workitem/:id/related` -> graph/result view.
- Batch flow:
  - task selection via SSE -> per-root related fetch -> commit-tag batch enrichment.

Figure placeholder:
- Figure 5 - UI component and data-flow architecture
- Suggested file: docs/figures/ui-architecture.png

---

## 6. Docker Orchestration View

### 6.1 Service-Level Orchestration

- Backend container:
  - exposes API endpoints,
  - connects to Azure DevOps through configured credentials.
- UI container:
  - serves trace screens,
  - targets backend base URL from environment configuration.

### 6.2 Orchestration Objectives

- isolate services for reproducible runtime behavior;
- standardize execution across developer and CI environments;
- simplify deployment by composing backend and UI as independent units.

### 6.3 Recommended Runtime Diagram Scope

The orchestration diagram should show:
- UI container,
- backend container,
- configuration/secret injection,
- outbound dependency to Azure DevOps APIs,
- request flow between all runtime components.

Figure placeholder:
- Figure 6 - Docker orchestration and runtime communication
- Suggested file: docs/figures/docker-orchestration.png

---

## 7. Suggested Figure Placement Summary

- Figure 1: technology stack topology
- Figure 2: Scrum workflow
- Figure 3: development lifecycle
- Figure 4: backend architecture
- Figure 5: UI architecture
- Figure 6: Docker orchestration

If needed, each figure can be generated from PlantUML and exported as PNG/SVG for report integration.

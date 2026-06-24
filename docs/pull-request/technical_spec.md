# Pull Request Module - Technical Specification

## Module Purpose
Provide a reusable controller/service layer that resolves work items associated with an Azure DevOps pull request. The module lives under `src/pull-request/` and exposes a single REST endpoint consumed by other modules and clients.

---

## Architecture & File Layout

```
pull-request.controller.ts  ->  PullRequestService
pull-request.service.ts     ->  AzureDevopsService (Git API + Work Item Tracking API)
                               ->  common/azure-devops/work-item-utils.ts (extractLinks)

DTOs: src/pull-request/dto/pull-request.dto.ts
```

###  Architecture Diagram

::: mermaid
flowchart TD
  C[PullRequestController] --> S[PullRequestService]
  S --> ADO[AzureDevopsService]
  S --> WU[work-item-utils]
  ADO --> GIT[Git API]
  ADO --> WIT[Work Item Tracking API]
:::

###  Class Diagram

::: mermaid
classDiagram
  class PullRequestController {
    +getWorkItemsByPRId(prId, project)
  }
  class PullRequestService {
    +getWorkItemsByPR(project, prId)
    +getWorkItemsResponseDataByPR(prId, project)
    -fetchWorkItemsRecursive(project, prId, visitedPRs)
    -fetchPRById(gitApi, prId, project)
  }
  class WorkItemsResponseDto
  class WorkItemsDataDto
  class WorkItemResultDto
  class LinkInfoDto

  PullRequestController --> PullRequestService
  PullRequestController --> WorkItemsResponseDto
  PullRequestService --> WorkItemsDataDto
  WorkItemsDataDto --> WorkItemResultDto
  WorkItemResultDto --> LinkInfoDto
:::

### Dependencies
- `AzureDevopsService` - provides authenticated clients for Git and Work Item Tracking APIs.
- `common/azure-devops/work-item-utils.ts` - used to normalize relation links.
- NestJS `Logger` - instrumentation for warnings/errors.

---

## Controllers

### `PullRequestController`
- Prefix: `pullrequests`
- Routes:
  | Method | Path | Handler | Description |
  |--------|------|---------|-------------|
  | GET | `/:prId/workitems` | `getWorkItemsByPRId()` | Validates `prId`, forwards to service, wraps `{ success, data }` |

**Validation Rules**
- `prId` must be numeric (`Number.isFinite`).
- `project` query parameter is optional and forwarded untouched.

---

## DTOs

Defined in `dto/pull-request.dto.ts`:
- `LinkInfo` - normalized relation metadata (`type`, `url`, `targetId`, `isPR`, `prId`).
- `WorkItemsResponse` - controller response envelope (`success`, `data`).

---

## Service Responsibilities

### `getWorkItemsResponseDataByPR(prId: number, project?: string)`
- Public entry point used by controllers.
- Resolves `project` to empty string when undefined.
- Calls `getWorkItemsByPR(project, prId)` and maps result into `{ prId, project, workItemCount, workItems }`.

### `getWorkItemsByPR(project: string, prId: number)`
- Main workhorse that fetches work item references for the PR.
- Delegates to `fetchWorkItemsRecursive(project, prId, visitedPRs)`.
- Exposed so other modules (e.g., Work Item traversal) can reuse it for PR expansion.

### `fetchWorkItemsRecursive(project, prId, visitedPRs)`
- Guards against infinite loops by short-circuiting when `prId` already visited.
- Steps:
  1. Obtain Git + Work APIs concurrently via `AzureDevopsService`.
  2. Call `fetchPRById()` to retrieve repo ID and metadata.
  3. Return empty list when `repoId` is unavailable.
  4. Resolve PR work item refs from Git API.
  5. Convert refs to numeric IDs and fetch work items with `WorkItemExpand.Relations`.
  6. Map to `WorkItemResult[]` with `{ id, title, links }`.
- Errors during guarded ref retrieval are logged and return an empty list.

### `fetchPRById(gitApi, prId, project?)`
- Tries `gitApi.getPullRequestById(prId, project)` first.
- If repo ID retrieved, optionally calls `gitApi.getPullRequest(repoId, prId, project)` as fallback.
- Logs warnings for failures and returns `undefined` when PR cannot be loaded.

### `getGitApi()` / `getWorkApi()`
- Thin wrappers over `AzureDevopsService` to obtain respective API clients.

---

## DTOs & Data Models

All DTOs located in `src/pull-request/dto/`:

### `LinkInfoDto` (class-validator)
Normalized relation link metadata.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `prId` | number | Yes | Parsed PR ID when `isPR` is true |
| `type` | string | Yes | Relation type (e.g., "ArtifactLink") |
| `targetId` | string | Yes | Raw target identifier in Azure DevOps |
| `url` | string | Yes | Absolute relation URL |
| `isPR` | boolean | No | True if relation points to a pull request |

### `WorkItemResultDto` (class-validator)
Single work item in PR response.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `id` | number | No | Work item ID |
| `title` | string | Yes | Work item title |
| `links` | LinkInfoDto[] | No | Array of relations/links |

### `WorkItemsDataDto` (class-validator)
Data envelope for pull request work items response.

| Field | Type | Notes |
|-------|------|-------|
| `prId` | number | Pull request ID (echo of request) |
| `project` | string | Project name resolved for the request |
| `workItemCount` | number | Number of work items returned |
| `workItems` | WorkItemResultDto[] | Array of work items linked to PR |

### `WorkItemsResponseDto` (class-validator)
Complete HTTP response envelope for PR endpoint.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `success` | boolean | No | True on success; false for errors |
| `data` | WorkItemsDataDto | No | Response payload containing PR work items |

---

## Performance Characteristics
- Work item fetches are executed in parallel using `Promise.all(ids.map(...))`.
- No caching inside the service; callers (e.g., Work Item module) implement their own per-request caches.
- `visitedPRs` set prevents repeated processing of the same PR ID.

---

## Future Enhancements (Backlog)
- Add batching for work item fetches if ID lists become large.
- Support returning PR metadata (title, repository, status) as part of the response.
- Consider an IDs-only helper for use cases that only need work item IDs (to reduce payload size).
- Introduce configurable concurrency limits / retries for Git API calls.

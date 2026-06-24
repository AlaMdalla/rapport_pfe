# Work Item Module - Technical Specification

## 1. Purpose
Expose read-only work item operations through NestJS endpoints with batching, retry, relation parsing, and recursive related-item traversal.

---

## 2. Architecture Overview

```
work-item.controller.ts
   -> stream-manager-service.ts
   -> work-item.service.ts
      -> common/azure-devops/work-item-utils.ts
      -> work-item-graph.utils.ts
      -> pull-request.service.ts
      -> Azure DevOps Work Item Tracking API
```

### Mermaid Architecture Diagram

::: mermaid
flowchart TD
  C[WorkItemController] --> WIS[WorkItemService]
  C --> SMS[StreamManagerService]
  SMS --> SS[StreamService]
  WIS --> ADO[AzureDevopsService]
  WIS --> PRS[PullRequestService]
  WIS --> WU[work-item-utils]
  WIS --> WG[work-item-graph.utils]
  ADO --> WIT[Work Item Tracking API]
:::

### Mermaid Class Diagram

::: mermaid
classDiagram
  class WorkItemController {
    +streamTasks(response)
    +getWorkItem(id)
    +getRelatedWorkItems(id, project)
  }
  class WorkItemService {
    +getTaskIds(project)
    +getWorkItems(ids, batchSize, onBatchFetched)
    +getWorkItemById(workItemId, useCache)
    +getRelatedWorkItems(rootWorkItemId, project)
  }
  class StreamManagerService
  class StreamService
  class PullRequestService
  class WorkItemDto
  class WorkItemLinkDto
  class WorkItemDetailsResultDto

  WorkItemController --> WorkItemService
  WorkItemController --> StreamManagerService
  StreamManagerService --> StreamService
  WorkItemService --> PullRequestService
  WorkItemService --> WorkItemDto
  WorkItemDto --> WorkItemLinkDto
  WorkItemService --> WorkItemDetailsResultDto
:::

Key points:
- `WorkItemController` handles request validation and response envelopes.
- `WorkItemService` owns Azure DevOps data access, cache management, and relationship traversal orchestration.
- `work-item-graph.utils.ts` contains pure traversal helper functions.
- `StreamManagerService` + `StreamService` handle SSE lifecycle and broadcasting.

---

## 3. File Layout

| File | Responsibility |
|------|----------------|
| `src/work-item/work-item.controller.ts` | HTTP endpoints under `/workitem` |
| `src/work-item/work-item.service.ts` | Main orchestration for fetch and related traversal |
| `src/work-item/work-item-graph.utils.ts` | Pure helper functions for graph traversal/caching |
| `src/work-item/stream-manager-service.ts` | SSE stream lifecycle and client management |
| `src/common/azure-devops/work-item-utils.ts` | Shared Azure relation parsing (`extractLinks`, `parseWorkItemIdFromLink`) |

---

## 3.5 Data Models & DTOs

All DTOs located in `src/work-item/dto/`:

### `WorkItemDto` (class-validator)
Normalized work item representation.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `id` | number | Yes | Work item ID |
| `type` | string \| null | Yes | Azure DevOps work item type (Task, Bug, etc.) |
| `title` | string \| null | Yes | Work item title |
| `state` | string \| null | Yes | Current state (Active, Closed, etc.) |
| `status` | string \| null | Yes | Status field if available |
| `assignedTo` | string \| null | Yes | Display name of assigned user |
| `links` | WorkItemLinkDto[] | No | Array of relations |

### `WorkItemLinkDto` (class-validator)
Represents a relation/link from a work item.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `type` | string | Yes | Relation type (e.g., "ArtifactLink", "Relates") |
| `targetId` | string | Yes | Raw target identifier in Azure DevOps |
| `url` | string | Yes | Absolute URL to the linked resource |
| `isPR` | boolean | No | True if link points to a pull request |
| `prId` | number | Yes | Parsed PR ID when `isPR` is true |

### `WorkItemDetailsResultDto` (class-validator)
Response DTO for `/workitem/:id/related` endpoint.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `workItem` | WorkItemDto | No | Root work item requested |
| `workItemId` | number | No | ID of root work item (for validation) |
| `project` | string | No | Project name used in traversal |
| `prRelatedCount` | number | No | Count of unique items related via PRs |
| `childrenCount` | number | No | Count of direct child items |
| `totalUniqueCount` | number | No | Total unique work items in traversal |
| `prRelatedItems` | WorkItemDto[] | No | All items related through pull requests |
| `childItems` | WorkItemDto[] | No | Direct child items from hierarchy links |
| `allUniqueIds` | number[] | No | Deduplicated list of all item IDs |
| `allCommits` | Map<string, string> | Yes | Commit hash → message mapping if available |

### `RelatedWorkItemsResponseDto` (class-validator)
Response envelope for `/workitem/:id/related` endpoint.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `success` | boolean | No | Always true on success |
| `data` | RelatedWorkItemsDataDto | No | Response payload |

### `RelatedWorkItemsDataDto` (class-validator)
Response payload for `/workitem/:id/related` endpoint.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `project` | string | No | Project name (or `N/A` if not specified) |
| `workItemId` | number | No | Root work item ID |
| `relatedCount` | number | No | Total unique related work items |
| `workItems` | WorkItemDto[] | No | All discovered work items |
| `visitedPullRequestIds` | number[] | No | All PR IDs encountered during traversal |
| `commitCount` | number | No | Total commits found |
| `commits` | CommitInfo[] | No | Commit information |

### `RelatedWorkItemsBatchResponseDto` (class-validator)
Response envelope for `/workitem/related` (batch) endpoint.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `success` | boolean | No | Always true on success |
| `data` | RelatedWorkItemsBatchDataDto | No | Response payload |

### `RelatedWorkItemsBatchDataDto` (class-validator)
Response payload for `/workitem/related` (batch) endpoint.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `project` | string | No | Project name (or `N/A` if not specified) |
| `requestedWorkItemIds` | number[] | No | List of root work item IDs queried |
| `relatedCount` | number | No | Total unique related work items |
| `workItems` | WorkItemDto[] | No | All discovered work items across all roots |
| `visitedPullRequestIds` | number[] | No | All PR IDs encountered during traversal |
| `commitCount` | number | No | Total commits found |
| `commits` | CommitInfo[] | No | Commit information |

### `CommitInfo` (class-validator)
Represents a commit discovered during traversal.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `commitId` | string | No | Git commit SHA hash |
| `repoName` | string | No | Repository name |

### `StreamLevelEventDto` (class-validator)
SSE event emitted during `GET /workitem/tasks/stream` for each traversal level.

| Field | Type | Notes |
|-------|------|-------|
| `type` | 'level' | Literal string identifying event type |
| `level` | number | Depth level (0 = root tasks) |
| `items` | WorkItemDto[] | Work items discovered at this level |

### `StreamCompleteSummaryDto` (class-validator)
Summary metadata for stream completion.

| Field | Type | Optional | Notes |
|-------|------|----------|-------|
| `totalLevels` | number | No | Number of levels traversed |
| `totalItems` | number | No | Total work items fetched |
| `itemsReturned` | number | No | Items actually returned (after dedup) |
| `prsVisited` | number[] | No | PR IDs visited during expansion |
| `commits` | Record<string, string> | Yes | Commit hash → message map |

### `StreamCompleteEventDto` (class-validator, extends StreamCompleteSummaryDto)
SSE event emitted at stream completion with final summary.

| Field | Type | Notes |
|-------|------|-------|
| `type` | 'complete' | Literal string identifying event type |
| (inherited) | StreamCompleteSummaryDto | All summary fields |

---

## 4. Implemented Endpoints

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/workitem/tasks/stream` | SSE stream of progressive task batches |
| `GET` | `/workitem/:id` | Returns `{ success, data }` for one work item |
| `GET` | `/workitem/:id/related` | Returns deduplicated recursively related items for single root |
| `GET` | `/workitem/related` | Returns deduplicated related items for multiple roots (batch) |

---

## 5. WorkItemService Internals

### Cache Configuration
- `maxCacheSize = 1000` for cross-request work item cache (`workItemCache`)
- `maxPrCacheSize = 1000` for per-request PR expansion cache (`prToWorkItemIds`)
- Both use FIFO eviction: when limit exceeded, oldest key is removed

### Dependencies
- `AzureDevopsService` for Work Item Tracking API clients.
- `PullRequestService` for PR-to-work-item expansion.
- `extractLinks` from shared Azure helper utilities.

### Core methods
- `getTaskIds(project)`
  - Runs WIQL for `Task`, `Bug`, `User Story` IDs.
- `getWorkItems(ids, batchSize = 200, onBatchFetched?)`
  - Splits IDs into batches.
  - Fetches all batches concurrently.
  - Retries each failed batch once.
  - Maps Azure items into normalized `WorkItem` payloads.
- `getWorkItemById(workItemId, useCache = true)`
  - Retrieves one work item with `WorkItemExpand.Relations`.
  - Uses cross-request `workItemCache` with max size eviction (max 1000 entries).
- `getRelatedWorkItems(rootWorkItemId, project = '')`
  - Loads the root item, then delegates traversal to a private recursive helper.
  - Maintains:
    - `discoveredIds` for deduplication
    - `fetchedWorkItems` per-request cache
    - `prToWorkItemIds` per-request PR expansion cache with max size eviction (max 1000 entries)
  - Expands PR-linked work items via `expandPullRequests`.

### Supporting private methods
- `fetchWorkItemsBatch(ids)`
- `getRootOrFail(rootWorkItemId)`
  - Validates that the root item exists and converts missing roots into `NotFoundException`.
- `getPrRelatedIdsForLevel(presentItems, project, prToWorkItemIds)`
  - Extracts PR IDs from the current level and expands them when needed.
- `addDiscoveredIds(discoveredIds, nextLevelIds)`
  - Adds newly discovered IDs to the traversal deduplication set.
- `traverseLevel(levelIds, project, fetchedWorkItems, prToWorkItemIds, discoveredIds, results)`
  - Processes one traversal level, fetches new work items, resolves PR-linked IDs, and recurses.
- `expandPullRequests(prIds, project, cache)`
  - Fetches work items linked to pull requests with concurrency limit of 5.
  - Caches successful PR expansions only.
  - Enforces `maxPrCacheSize` limit: when cache exceeds limit, removes oldest (first-inserted) entry.
  - Returns flattened array of all work item IDs across all PR expansions.

---

## 6. Graph Utility Functions

`src/work-item/work-item-graph.utils.ts` provides pure functions used by traversal:
- `cacheFetchedWorkItems`
- `getPresentLevelItems`
- `extractUniquePrIds`
- `computeNextLevelIds`

These helpers keep link/graph transformations separate from service orchestration logic.

The helper functions are intentionally stateless so they can be reused without introducing service-level dependencies into traversal math.

---

## 7. Streaming Implementation

Streaming uses SSE, not NDJSON.

Flow:
1. `StreamService.setSseHeaders` sets:
   - `Content-Type: text/event-stream`
   - `Cache-Control: no-cache`
   - `Connection: keep-alive`
2. `StreamManagerService` tracks connected clients.
3. `getTaskIds` + `getWorkItems` run progressively.
4. Each fetched batch is broadcast as `data: { batch, batchNumber, totalLoaded }`.
5. Completion broadcasts `data: { complete: true, totalTasks, batchesProcessed }` and closes clients.
6. Error broadcasts `data: { error }` and closes clients.

---

## 8. Error and Retry Behavior

- Invalid IDs produce `BadRequestException` in controller.
- Missing root work item produces `NotFoundException`.
- Batch fetch failures retry once; second failure throws.
- PR expansion failures are logged and skipped for that PR.
- Traversal continues to the next level even if the current level has no PR links.

---

## 9. Performance Characteristics

- Batch size defaults to 200 work item IDs.
- Batch retrieval uses `Promise.all` concurrency.
- Traversal uses caching + deduplication to avoid repeated calls.
- Service-level `workItemCache` prevents repeated single-item fetches across requests.

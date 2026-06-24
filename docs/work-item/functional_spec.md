# Work Item Module - Functional Specification

## 1. Module Overview

**Module name:** Work Item Module

**Purpose:** Provide read-only APIs for work item lookup, related-item traversal, and progressive task streaming from Azure DevOps.

**Description:** The module exposes endpoints under `/workitem`, validates IDs at controller level, and delegates Azure DevOps orchestration to `WorkItemService` and `StreamManagerService`.

---

## 2. Functional Scope

### Included in current implementation
- Stream task work items via SSE: `GET /workitem/tasks/stream`
- Get a single work item by ID: `GET /workitem/:id`
- Get recursively related work items (hierarchy children + PR-linked items): `GET /workitem/:id/related`
- Get related work items for multiple root IDs in one call: `GET /workitem/related` (batch)

### Related-item traversal behavior
- The related-item endpoint starts from a root work item and traverses the graph level by level.
- Each level includes direct child links and, when present, work items expanded from linked pull requests.
- Traversal keeps a `discoveredIds` set to avoid visiting the same work item more than once.
- PR expansion failures are logged and skipped for that PR only; traversal continues with the rest of the graph.
- The service returns the related items it was able to collect, even when one traversal level fails.

### Not implemented in current controller
- `GET /workitem/health`
- `GET /workitem/:id/pullrequests`
- Any create/update/delete operation

---

## 3. API Endpoints

### 3.1 `GET /workitem/tasks/stream`
- **Transport:** SSE (`text/event-stream`)
- **Behavior:**
  1. Controller uses fixed project value `MES_X.0`.
  2. Task IDs are resolved via WIQL (`Task`, `Bug`, `User Story`).
  3. Work items are fetched in batches of 200.
  4. Each batch is emitted as SSE event data with:
     - `batch`
     - `batchNumber`
     - `totalLoaded`
  5. Final completion event includes:
     - `complete: true`
     - `totalTasks`
     - `batchesProcessed`

### 3.2 `GET /workitem/:id`
- **Path params:** `id` (required numeric string)
- **Behavior:**
  1. Validate `id`; invalid values return `400`.
  2. Fetch work item via `getWorkItemById`.
  3. Return `{ success: true, data: workItem }`.
  4. Return `404` when no work item is found.

### 3.3 `GET /workitem/:id/related`
- **Path params:** `id` (required numeric string)
- **Query params:** `project` (optional string, default empty string in service call)
- **Behavior:**
  1. Validate `id` and ensure root work item exists.
  2. Traverse related graph from root using:
     - child hierarchy links
     - PR links expanded through Pull Request module
  3. Deduplicate traversal using a discovered-ID set so nodes are not revisited.
  4. Continue traversal even when a level has no PR links.
  3. Return:
     - `success: true`
     - `data.project` (`project` query value or `N/A`)
     - `data.workItemId`
     - `data.relatedCount`
     - `data.workItems`
     - `data.visitedPullRequestIds`
     - `data.commits`
     - `data.commitCount`

### 3.4 `GET /workitem/related` (Batch)
- **Query params:**
  - `workItemIds` (required): Comma-separated list of work item IDs (max 100)
  - `project` (optional): Azure DevOps project name (default empty string)
- **Behavior:**
  1. Validate `workItemIds` and ensure all root work items exist.
  2. For each root work item ID, traverse the related graph using:
     - child hierarchy links
     - PR links expanded through Pull Request module
  3. Deduplicate traversal across all root items using a single `discoveredIds` set so nodes are not revisited.
  4. Return aggregated results:
     - `success: true`
     - `data.project` (provided `project` query value or `N/A`)
     - `data.requestedWorkItemIds` (list of root IDs that were queried)
     - `data.relatedCount` (total unique work items discovered)
     - `data.workItems` (all discovered work items)
     - `data.visitedPullRequestIds` (all PR IDs encountered during traversal)
     - `data.commitCount` (total commits found)
     - `data.commits` (all commits from visited PRs)

---

## 4. Behavioral Rules

### Caching Strategy
- **Cross-request work item cache** (`workItemCache`):
  - Stores up to 1,000 work items (max size)
  - Shared across all requests
  - Uses FIFO eviction: when limit exceeded, oldest entry is removed
  - Prevents redundant fetches of frequently accessed items

- **Per-request caches** (used during single `/related` traversal):
  - `fetchedWorkItems`: caches work items fetched in current traversal
  - `prToWorkItemIds`: caches PR-to-work-item expansions (max 1,000 entries)
    - Uses FIFO eviction when limit exceeded
    - Caches successful PR expansions only; failed PR expansions are logged and retried on later traversals

### Traversal & Error Handling
- Related traversal deduplicates IDs using `discoveredIds` set
- Related traversal computes the next level even when no PR links exist at that level
- PR expansion failures are logged and treated as empty expansion for that PR
- Batch work item retrieval retries once per failed batch before throwing
- One failed PR expansion does not fail the entire traversal

---

## 5. Data Models

### WorkItem
Core work item representation used throughout endpoints.

```typescript
{
  id: number,
  type: string | null,
  title: string | null,
  state: string | null,
  status: string | null,
  assignedTo: string | null,
  links: WorkItemLink[]
}
```

**Fields:**
- `id` - Unique Azure DevOps work item identifier
- `type` - Work item type (Task, Bug, User Story, etc.)
- `title` - Work item title/name
- `state` - Current state (Active, Closed, Resolved, etc.)
- `status` - Status field (if different from state)
- `assignedTo` - Display name of assigned user, or "Unassigned"
- `links` - Array of related work items and pull requests

### WorkItemLink
Represents a relation/link to another work item or PR.

```typescript
{
  type: string,
  targetId: string,
  url: string,
  isPR: boolean,
  prId?: number
}
```

**Fields:**
- `type` - Relation type (ArtifactLink, Relates, Parent, Child, etc.)
- `targetId` - Raw Azure DevOps target identifier
- `url` - Absolute URL to the linked resource
- `isPR` - True if this link points to a pull request
- `prId` - Parsed PR ID (populated when `isPR` is true)

### StreamEvent (SSE)
Events emitted during `/workitem/tasks/stream` traversal.

**Level Event:**
```typescript
{
  type: "level",
  level: number,
  items: WorkItem[]
}
```

**Complete Event:**
```typescript
{
  type: "complete",
  totalLevels: number,
  totalItems: number,
  itemsReturned: number,
  prsVisited: number[],
  commits?: Record<string, string>
}
```

### Related Items Response
Structure returned by `/workitem/:id/related`.

```typescript
{
  success: true,
  data: {
    project: string,
    workItemId: number,
    relatedCount: number,
    workItems: WorkItem[],
    visitedPullRequestIds: number[],
    commits: CommitInfo[],
    commitCount: number
  }
}
```

### Related Items Batch Response
Structure returned by `/workitem/related` (batch endpoint).

```typescript
{
  success: true,
  data: {
    project: string,
    requestedWorkItemIds: number[],
    relatedCount: number,
    workItems: WorkItem[],
    visitedPullRequestIds: number[],
    commits: CommitInfo[],
    commitCount: number
  }
}
```

### CommitInfo
Represents a commit discovered during work item traversal.

```typescript
{
  commitId: string,
  repoName: string
}
```

**Fields:**
- `commitId` - Git commit SHA hash
- `repoName` - Repository name where commit was found

# Commit Module - Technical Specification

## 1. Purpose
Expose read-only commit operations through NestJS endpoints, including commit retrieval by pull request/work item and branch/tag resolution for a commit.

---

## 2. Architecture Overview

```
commit.controller.ts
   -> commit.service.ts
      -> commit-pr.service.ts
      -> commit-work-item.service.ts
      -> commit-history.service.ts

commit-pr.service.ts
   -> AzureDevopsService (Git API)

commit-work-item.service.ts
   -> WorkItemService
   -> commit-pr.service.ts
   -> commit-url.utils.ts
   -> common/azure-devops/work-item-utils.ts

commit-history.service.ts
   -> AzureDevopsService (Git API)
   -> commit-reference.utils.ts
  -> tag-resolution.utils.ts
  -> tag-selection.utils.ts
```

### Mermaid Architecture Diagram

::: mermaid
flowchart TD
  C[CommitController] --> S[CommitService]
  S --> PR[CommitPRService]
  S --> WI[CommitWorkItemService]
  S --> H[CommitHistoryService]
  PR --> ADO[AzureDevopsService]
  WI --> WIS[WorkItemService]
  WI --> PR
  WI --> URL[commit-url.utils]
  WI --> WU[work-item-utils]
  H --> ADO
  H --> REF[commit-reference.utils]
  H --> TAGR[tag-resolution.utils]
  H --> TAGS[tag-selection.utils]
:::

### Mermaid Class Diagram

::: mermaid
classDiagram
  class CommitController {
    +getCommitsByWorkitem(workItemId, project)
    +getCommitsByPR(prId, project)
    +getRepoBranchesAndTags(project, repositoryName)
    +getTagsByCommit(query)
    +getTagsByCommitBatch(query)
  }
  class CommitService {
    +getCommitsByWorkitem(project, workItemId)
    +getCommitsByPR(project, pullRequestId)
    +getRepoBranchesAndTags(project, repositoryName)
    +getBranchesAndTagsByCommit(project, repositoryName, commitId)
    +getBranchesAndTagsByCommitBatch(project, repositoryName, commitIds)
  }
  class CommitPRService
  class CommitWorkItemService
  class CommitHistoryService
  class RepoReferencesResponseDto

  CommitController --> CommitService
  CommitService --> CommitPRService
  CommitService --> CommitWorkItemService
  CommitService --> CommitHistoryService
  CommitHistoryService --> RepoReferencesResponseDto
:::

Key points:
- `CommitController` defines HTTP contracts and delegates all logic to `CommitService`.
- `CommitService` acts as orchestration facade over three specialized services.
- `CommitPRService` handles pull-request-to-commits resolution.
- `CommitWorkItemService` resolves commits from work item links and linked PRs.
- `CommitHistoryService` handles branches/tags listing and branch/tag-by-commit lookups.

---

## 3. File Layout

| File | Responsibility |
|------|----------------|
| `src/commit/commit.controller.ts` | HTTP routes under `/commits` |
| `src/commit/service/commit.service.ts` | Delegation facade over specialized commit services |
| `src/commit/service/commit-pr.service.ts` | Resolve commits for a pull request |
| `src/commit/service/commit-work-item.service.ts` | Resolve commits linked to a work item |
| `src/commit/service/commit-history.service.ts` | Branch/tag listing and branch/tag by commit |
| `src/commit/utils/commit-reference.utils.ts` | Ref traversal helpers for commit containment checks |
| `src/commit/utils/tag-resolution.utils.ts` | Repository/target commit and tag resolution helpers |
| `src/commit/utils/tag-selection.utils.ts` | Tag selection strategy (exact vs surrounding tags) |
| `src/commit/utils/commit-url.utils.ts` | Commit hash extraction from Azure artifact links |

---

## 4. Implemented Endpoints

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/commits/workitems/:workItemId` | Commits linked to a work item |
| `GET` | `/commits/pullrequests/:prId` | Commits linked to a pull request |
| `GET` | `/commits/branches` | Repository branches and tags |
| `GET` | `/commits/tags` | Branches and tags related to a specific commit |
| `GET` | `/commits/tags/batch` | Batch tag context resolution for multiple commits |

Controller-level exception handling uses `@UseFilters(MesGenericErrorFilter)`.

---

## 5. Service Internals

### 5.1 CommitService
- Thin facade that routes each endpoint use case to:
  - `CommitPRService`
  - `CommitWorkItemService`
  - `CommitHistoryService`
- Includes both single and batch tag-resolution delegations:
  - `getBranchesAndTagsByCommit(...)`
  - `getBranchesAndTagsByCommitBatch(...)`

### 5.2 CommitPRService
- Uses Git API from `AzureDevopsService`.
- Steps:
  1. Fetch PR by ID.
  2. Resolve repository ID and name.
  3. Fetch PR commits.
  4. Deduplicate commits using `Map<string, CommitInfo>`.
- If repository is not found for the PR, returns a valid empty result (`commitCount: 0`, `commits: []`).

### 5.3 CommitWorkItemService
- Uses `WorkItemService` to fetch work item details.
- Reads links from either `workItem.links` or `extractLinks(workItem)`.
- Separates links into:
  - PR links (`isPR` + `prId`)
  - direct commit links parsed via `extractCommitIdFromUrl`
- Resolves PR commits with bounded concurrency (`p-limit(5)`).
- Merges/deduplicates all commit sources with `Map<string, CommitInfo>`.
- Logs and skips failed PR commit lookups while continuing aggregation.

### 5.4 CommitHistoryService
- `getRepoBranchesAndTags(project, repositoryName)`:
  - resolves repository
  - reads refs
  - splits refs into `refs/heads/*` and `refs/tags/*`
  - returns `success: false` with message if repository is missing
- `getBranchesAndTagsByCommit(project, repositoryName, commitId)`:
  - resolves all refs once
  - verifies target commit existence first
  - resolves tag target commits (annotated and lightweight tags)
  - returns exact tag matches; otherwise nearest surrounding tags (before/after)
  - performs branch containment scan only when no tags are resolved
  - returns `success: false` with message for repository-not-found, commit-not-found, or processing failure
- `getBranchesAndTagsByCommitBatch(project, repositoryName, commitIds)`:
  - validates `commitIds` (non-empty, max 100)
  - resolves all tags and selects the latest resolved tag by date
  - finds matching branches containing that latest tag commit
  - selects one branch deterministically via lexicographical sort (`pickBranchRef`)
  - scans only the selected branch history for all requested commits
  - returns `BatchTagsResponseDto` with per-commit context (`exactTags`, `tagAfter`, `tagBefore`, `foundInBranch`)

---

## 6. DTOs and Response Contracts

Main DTOs (`src/commit/dto/`):
- `CommitInfo`:
  - `commitId: string`
  - `repoName: string`
- `CommitsByPRDataDto`:
  - `prId: number`
  - `project: string`
  - `commitCount: number`
  - `commits: CommitInfo[]`
- `CommitsByWorkItemDataDto`:
  - `workItemId: number`
  - `project: string`
  - `commitCount: number`
  - `commits: CommitInfo[]`
- `CommitsByPRResponseDto` and `CommitsByWorkItemResponseDto`:
  - `success: boolean`
  - `data: ...`
- `RepoReferencesResponseDto`:
  - `success: boolean`
  - `message?: string`
  - `branches: string[]`
  - `tags: string[]`
- `BatchTagsResponseDto`:
  - `success: boolean`
  - `message?: string`
  - `results: Record<string, CommitTagContextDto>`
- `CommitTagContextDto`:
  - `exactTags: string[]`
  - `tagAfter: string[]`
  - `tagBefore: string[]`
  - `foundInBranch: boolean`

---

## 7. Error Handling and Logging

- Controller layer is guarded by `MesGenericErrorFilter`.
- Services log structured context for traceability:
  - operation name
  - entity identifiers (PR ID, work item ID, commit ID, repository name)
- Failure strategy differs by use case:
  - PR/work item services rethrow hard failures.
  - history/ref flows return `success: false` DTOs with failure messages for not-found/error scenarios.

---

## 8. Performance Characteristics

- PR commit and work item commit deduplication via hash-map structures.
- PR expansion in work item flow limited with `p-limit(5)` to control upstream pressure.
- Branch/tag lookup fetches refs once per request and reuses that set.
- Tag resolution attempts annotated resolution first, then falls back to lightweight lookup.
- Branch lookup in tags-by-commit is conditional and runs only when tag resolution returns no tags.
- Batch tag resolution scans one selected branch history for all commit IDs to keep latency bounded.

---

## 9. Known Technical Notes

- Work item commit resolution may produce `unknown-repository` for direct commit links where repository context is not available from link payload.
- Reference DTOs support explicit failure messages via optional `message`.
- Shared logger helpers (`getErrorMessage`, `getErrorStack`) are used instead of local service error helper duplication.

---

## 10. Future Improvements

- Add optional date range filters for tags-by-commit lookup.
- Add short-lived cache for repository refs and commit ancestry checks.
- Introduce configurable concurrency and retry policy for Azure DevOps operations.

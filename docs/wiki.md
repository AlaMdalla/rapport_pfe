# MES-X Dependency Management - Implementation Wiki

Dependency Management microservice for MES-X. It exposes work-item, pull-request, commit, sprint, decision, and LLM-backed review capabilities so other services and trace screens can follow work and code changes.

This wiki documents the implementation that exists in the repository today. It focuses on the current backend contracts and the internal module structure that is actually running now.

---

## Overview

Current modules:

- **Work Item Module** - owns `/workitem/*` endpoints
- **Pull Request Module** - owns `/pullrequests/*` endpoints
- **Commit Module** - owns `/commits/*` endpoints
- **Sprint Module** - owns `/sprint/*` endpoints
- **Decision Module** - owns `/decision/*` endpoints
- **LLM Module** - supports commit review prompt building and review generation through commit endpoints

> Notification capabilities can be referenced for context but are outside this repository scope.

---

## Implemented Architecture (Current)

The following architecture is implemented in this repository today.

::: mermaid
flowchart LR
   Client[Client or API Gateway]

   subgraph Controllers[Controllers]
      WorkItemController[WorkItemController]
      PullRequestController[PullRequestController]
      CommitController[CommitController]
      SprintController[SprintController]
      DecisionController[DecisionController]
   end

   subgraph CoreServices[Core Services]
      WorkItemService[WorkItemService]
      WorkItemCommitService[WorkItemCommitService]
      StreamManagerService[StreamManagerService]
      PullRequestService[PullRequestService]
      CommitService[CommitService]
      CommitPRService[CommitPRService]
      CommitWorkItemService[CommitWorkItemService]
      CommitHistoryService[CommitHistoryService]
      SprintService[SprintService]
      DecisionAggregateService[DecisionAggregateService]
   end

   subgraph LlmServices[LLM Services]
      LlmService[LlmService]
      LlmReviewPromptService[LlmReviewPromptService]
      LlmGuidanceService[LlmGuidanceService]
   end

   subgraph SharedInfra[Shared Infrastructure]
      AzureDevopsService[AzureDevopsService]
      CacheManagerService[CacheManagerService]
      AppLogger[AppLogger]
   end

   WorkApi[(Azure DevOps Work Item API)]
   GitApi[(Azure DevOps Git API)]
   Gemini[(Gemini API)]

   Client --> WorkItemController
   Client --> PullRequestController
   Client --> CommitController
   Client --> SprintController
   Client --> DecisionController

   WorkItemController --> WorkItemService
   WorkItemController --> StreamManagerService
   PullRequestController --> PullRequestService
   CommitController --> CommitService
   CommitController --> LlmService
   SprintController --> SprintService
   DecisionController --> DecisionAggregateService

   CommitService --> CommitPRService
   CommitService --> CommitWorkItemService
   CommitService --> CommitHistoryService
   CommitWorkItemService --> WorkItemService
   CommitWorkItemService --> CommitPRService
   WorkItemService --> PullRequestService
   WorkItemService --> WorkItemCommitService

   LlmService --> LlmReviewPromptService
   LlmReviewPromptService --> LlmGuidanceService

   WorkItemService --> AzureDevopsService
   PullRequestService --> AzureDevopsService
   CommitPRService --> AzureDevopsService
   CommitHistoryService --> AzureDevopsService
   SprintService --> AzureDevopsService
   LlmService --> AzureDevopsService

   WorkItemService --> CacheManagerService
   LlmGuidanceService --> AppLogger
   DecisionAggregateService --> AppLogger

   AzureDevopsService --> WorkApi
   AzureDevopsService --> GitApi
   LlmService --> Gemini
:::

---

## Data Models (Current)

The diagrams below follow the DTOs that are implemented in the current backend, but they intentionally keep only the most important classes so the model stays readable.

### Global Class Diagram (Current)

::: mermaid
classDiagram
   direction LR

   class WorkItemLinkDto {
      +type: string?
      +targetId: string?
      +url: string?
      +isPR: boolean
      +prId: number?
   }

   class WorkItemDto {
      +id: number?
      +type: string?
      +title: string?
      +state: string?
      +status: string?
      +assignedTo: string?
      +links: WorkItemLinkDto[]
   }

   class PullRequestSummaryDto {
      +prId: number
      +repositoryName: string
   }

   class CommitInfo {
      +commitId: string
      +repoName: string
   }

   class RelatedWorkItemsDataDto {
      +project: string
      +workItemId: number
      +relatedCount: number
      +visitedPullRequestIds: number[]
      +commitCount: number
   }

   class WorkItemsDataDto {
      +prId: number
      +project: string
      +workItemCount: number
   }

   class CommitTagContextDto {
      +exactTags: string[]
      +tagAfter: string[]
      +tagBefore: string[]
      +foundInBranch: boolean
   }

   class SprintDto {
      +id: string
      +name: string
      +path: string
   }

   class DecisionInputWorkItemDto {
      +id: number
      +state: string?
   }

   class RepoReferenceWithNameDto {
      +repositoryName: string
   }

   class DecisionInputSetDto {
      +workItems: DecisionInputWorkItemDto[]
      +repositories: RepoReferenceWithNameDto[]
   }

   class RepoBeforeAfterDto {
      +repositoryName: string
   }

   class DecisionAggregateResultDto {
      +doneWorkItems: DecisionInputWorkItemDto[]
      +otherWorkItems: DecisionInputWorkItemDto[]
   }

   WorkItemDto "1" --> "0..*" WorkItemLinkDto : links
   RelatedWorkItemsDataDto "1" --> "0..*" WorkItemDto : workItems
   RelatedWorkItemsDataDto "1" --> "0..*" PullRequestSummaryDto : visitedPullRequests
   RelatedWorkItemsDataDto "1" --> "0..*" CommitInfo : commits
   WorkItemsDataDto "1" --> "0..*" WorkItemDto : workItemsFromPR
   DecisionInputSetDto "1" --> "0..*" DecisionInputWorkItemDto : workItems
   DecisionInputSetDto "1" --> "0..*" RepoReferenceWithNameDto : repositories
   DecisionAggregateResultDto "1" --> "0..*" RepoBeforeAfterDto : repositoryGroups
:::

### Pull Request -> Work Items

::: mermaid
classDiagram
   direction LR

   class LinkInfoDto {
      +prId: number?
      +type: string?
      +targetId: string?
      +url: string?
      +isPR: boolean
   }

   class WorkItemResultDto {
      +id: number
      +title: string?
      +links: LinkInfoDto[]
   }

   class WorkItemsDataDto {
      +prId: number
      +project: string
      +workItemCount: number
   }

   WorkItemResultDto "1" --> "0..*" LinkInfoDto : links
   WorkItemsDataDto "1" --> "0..*" WorkItemResultDto : workItems
:::

### Work Item Traversal

::: mermaid
classDiagram
   direction LR

   class WorkItemDto {
      +id: number?
      +type: string?
      +title: string?
      +state: string?
      +status: string?
   }

   class PullRequestSummaryDto {
      +prId: number
      +repositoryName: string
   }

   class CommitInfo {
      +commitId: string
      +repoName: string
   }

   class RelatedWorkItemsDataDto {
      +project: string
      +workItemId: number
      +relatedCount: number
      +visitedPullRequestIds: number[]
      +commitCount: number
   }

   class RelatedWorkItemsBatchDataDto {
      +project: string
      +requestedWorkItemIds: number[]
      +relatedCount: number
      +visitedPullRequestIds: number[]
      +commitCount: number
   }

   RelatedWorkItemsDataDto "1" --> "0..*" WorkItemDto : workItems
   RelatedWorkItemsDataDto "1" --> "0..*" PullRequestSummaryDto : visitedPullRequests
   RelatedWorkItemsDataDto "1" --> "0..*" CommitInfo : commits
   RelatedWorkItemsBatchDataDto "1" --> "0..*" WorkItemDto : aggregatedWorkItems
   RelatedWorkItemsBatchDataDto "1" --> "0..*" PullRequestSummaryDto : aggregatedPRs
   RelatedWorkItemsBatchDataDto "1" --> "0..*" CommitInfo : aggregatedCommits
:::

### Commit Data Contracts

::: mermaid
classDiagram
   direction LR

   class CommitInfo {
      +commitId: string
      +repoName: string
   }

   class CommitsByPRDataDto {
      +prId: number
      +project: string
      +commitCount: number
   }

   class CommitsByWorkItemDataDto {
      +workItemId: number
      +project: string
      +commitCount: number
   }

   class RepoReferencesResponseDto {
      +success: boolean
      +branches: string[]
      +tags: string[]
      +message: string?
   }

   class CommitTagContextDto {
      +exactTags: string[]
      +tagAfter: string[]
      +tagBefore: string[]
      +foundInBranch: boolean
   }

   class BatchTagsResponseDto {
      +success: boolean
      +message: string?
   }

   CommitsByPRDataDto "1" --> "0..*" CommitInfo : commits
   CommitsByWorkItemDataDto "1" --> "0..*" CommitInfo : commits
   BatchTagsResponseDto "1" --> "0..*" CommitTagContextDto : resultsByCommit
:::

### Sprint Contracts

::: mermaid
classDiagram
   direction LR

   class SprintAttributesDto {
      +startDate: string?
      +finishDate: string?
      +timeFrame: string?
   }

   class SprintDto {
      +id: string
      +name: string
      +path: string
      +url: string
   }

   class SprintWorkItemDto {
      +id: number
      +url: string
   }

   class SprintWorkItemsResponseDto {
      +sprintId: string
      +count: number
   }

   SprintDto "1" --> "1" SprintAttributesDto : attributes
   SprintWorkItemsResponseDto "1" --> "0..*" SprintWorkItemDto : workItems
:::

### Decision Contracts

::: mermaid
classDiagram
   direction LR

   class DecisionInputWorkItemDto {
      +id: number
      +state: string?
   }

   class CommitInputDto {
      +commitId: string
      +tagBefore: string[]
      +tagAfter: string[]
      +exactTags: string[]
   }

   class RepoReferenceWithNameDto {
      +repositoryName: string
      +commits: CommitInputDto[]
   }

   class DecisionInputSetDto {
      +workItems: DecisionInputWorkItemDto[]
      +repositories: RepoReferenceWithNameDto[]
   }

   class CommitResultDto {
      +commitId: string
      +considerForPR: boolean?
   }

   class RepoBeforeAfterDto {
      +repositoryName: string
      +commits: CommitResultDto[]
   }

   class DecisionAggregateResultDto {
      +doneWorkItems: DecisionInputWorkItemDto[]
      +otherWorkItems: DecisionInputWorkItemDto[]
   }

   DecisionInputSetDto "1" --> "0..*" DecisionInputWorkItemDto : workItems
   DecisionInputSetDto "1" --> "0..*" RepoReferenceWithNameDto : repositories
   RepoReferenceWithNameDto "1" --> "0..*" CommitInputDto : commits
   DecisionAggregateResultDto "1" --> "0..*" DecisionInputWorkItemDto : done/other
   DecisionAggregateResultDto "1" --> "0..*" RepoBeforeAfterDto : repoGroups
   RepoBeforeAfterDto "1" --> "0..*" CommitResultDto : commits
:::

---

## Work Item Module

The Work Item module orchestrates Azure DevOps Work Item Tracking queries for MES-X. It resolves individual work items, recursive related graphs (hierarchy + PR-linked nodes), and streams task data for trace analysis.

### Endpoint matrix

| Endpoint | Method | Backend behavior | Current UI usage |
|------|---------|---------|---------|
| `/workitem/:id` | `GET` | Returns a single work item with normalized relations | Available through the shared API service; not the main trace page contract |
| `/workitem/:id/related` | `GET` | Traverses hierarchy children and PR-linked work items for one root ID using level batching and request-scoped caches | Primary related-items endpoint used by `RelatedWorkItemTrace` and by the current batch-results fan-out flow |
| `/workitem/related` | `GET` | Traverses multiple root IDs in one call and returns one aggregated, deduplicated payload keyed by `requestedWorkItemIds` | Exposed by backend, but not currently used by `BatchRelatedWorkItemTrace` |
| `/workitem/tasks/stream` | `GET` | Streams task batches over SSE for progressive loading | Used by `BatchWorkItemTrace` |

### Response types in active trace flows

- `WorkItemResponseDto`: canonical single work item response.
- `RelatedWorkItemsResponseDto`: single-root response with `workItemId`, `workItems`, `visitedPullRequestIds`, `visitedPullRequests`, `commits`, and counters.
- `RelatedWorkItemsBatchResponseDto`: aggregated backend batch response with `requestedWorkItemIds`, deduplicated `workItems`, `visitedPullRequestIds`, `visitedPullRequests`, `commits`, and counters.
- SSE task messages:
  - batch payload: `{ batch, batchNumber, totalLoaded }`
  - completion payload: `{ complete: true, totalTasks, batchesProcessed }`
  - error payload: `{ error }`

### Current UI behavior against work-item endpoints

1. `RelatedWorkItemTrace` submits one root work item ID and renders one `RelatedWorkItemsData` payload.
2. `BatchWorkItemTrace` loads selectable tasks from the SSE stream.
3. `BatchRelatedWorkItemTrace` reads selected IDs from the route query, calls the single related endpoint once per root, sorts the resulting cards by commit and related-item counts, then groups discovered commits by repository for batch tag resolution.

### References

- [Functional Spec](work-item/functional_spec.md)
- [Technical Spec](work-item/technical_spec.md)
- [UI API Quickstart](ui/ui-api-quickstart.md)
- Source: `src/work-item/work-item.controller.ts`, `src/work-item/service/work-item.service.ts`, `src/work-item/dto/related-work-items-data.dto.ts`, `src/work-item/dto/related-work-items-batch-data.dto.ts`

---

## Pull Request Module

The Pull Request module surfaces work items linked to a specific Azure DevOps pull request and standardizes a response shape for downstream consumers.

### Endpoints

1. **Get Work Items Linked to a PR**  
   URL: `/pullrequests/:prId/workitems`  
   Method: `GET`  
   Description: Looks up PR metadata, resolves linked work items, and returns normalized results.

### Response Types

- `WorkItemsResponseDto`: Wrapper exposing `prId`, `project`, and `workItems`.
- `WorkItemResultDto`: Lightweight DTO containing id, title, and link metadata in PR context.

### References

- [Functional Spec](pull-request/functional_spec.md)
- [Technical Spec](pull-request/technical_spec.md)
- Source: `src/pull-request/pull-request.controller.ts`, `src/pull-request/pull-request.service.ts`

---

## Commit Module

The Commit module provides commit traceability APIs across work items, pull requests, branches, and tags.

### Endpoints

1. **Get Commits Linked to a Work Item**  
   URL: `/commits/workitems/:workItemId`  
   Method: `GET`  
   Description: Returns deduplicated commits found from direct links and related PR expansion.

2. **Get Commits Linked to a Pull Request**  
   URL: `/commits/pullrequests/:prId`  
   Method: `GET`  
   Description: Returns commits associated with the given pull request.

3. **Get Repository Branches and Tags**  
   URL: `/commits/branches`  
   Method: `GET`  
   Description: Lists branch and tag names for a repository.

4. **Get Branches/Tags by Commit**  
   URL: `/commits/tags`  
   Method: `GET`  
   Description: Resolves branch and tag references related to a commit hash.

5. **Get Tags by Commit Batch**  
   URL: `/commits/tags/batch`  
   Method: `GET`  
   Description: Batch resolves exact or surrounding tags for multiple commits using latest-tag branch strategy.

### Response Types

- `CommitsByWorkItemResponseDto`
- `CommitsByPRResponseDto`
- `RepoReferencesResponseDto`
- `BatchTagsResponseDto`

### References

- [Functional Spec](commit/functional_spec.md)
- [Technical Spec](commit/technical_spec.md)
- Source: `src/commit/commit.controller.ts`, `src/commit/commit.service.ts`, `src/commit/service/commit-history.service.ts`, `src/commit/dto/batch-tags-response.dto.ts`

---

## Key Source Files

| Repo | File | Purpose |
|------|------|---------|
| Backend | `src/work-item/work-item.controller.ts` | Handles `/workitem/*` routes, validation, and response shaping |
| Backend | `src/work-item/service/work-item.service.ts` | Azure DevOps integration, traversal caches, deduplication, and related item orchestration |
| Backend | `src/pull-request/pull-request.service.ts` | Fetches PR metadata and builds `visitedPullRequests` repository summaries |
| Backend | `src/pull-request/dto/pull-request-summary.dto.ts` | DTO used to expose `{ prId, repositoryName }` in related-work-item payloads |
| Backend | `src/commit/commit.controller.ts` | Exposes `/commits/*` endpoints |
| Backend | `src/commit/service/commit-history.service.ts` | Branch and tag resolution, including `/commits/tags/batch` |
| Backend | `src/common/azure-devops/work-item-utils.ts` | Relation parsing helpers shared by modules |
| UI | `src/global-router/index.ts` | Registers the three trace routes under `/cnerr-ui/trace/*` |
| UI | `src/work-item-trace/store/trace-store.ts` | Holds trace state, SSE lifecycle, and endpoint loaders |
| UI | `src/work-item-trace/services/trace-api.service.ts` | Shared axios client, auth redirect handling, and backend bindings |
| UI | `src/work-item-trace/composables/use-batch-related-results.ts` | Current batch-results orchestration; fans out single related-item requests and batches commit-tag lookups |
| UI | `src/work-item-trace/views/related-work-item-graph-view.vue` | Single-root related-items trace screen |
| UI | `src/work-item-trace/views/batch-related-work-items-view.vue` | Batch results screen for selected work items |

---

## Roadmap Notes

- Notification flows can be integrated as a separate module consuming these APIs.
- Commit/work item/PR contracts are now available for cross-service traceability and reporting.
- The backend batch related-items endpoint is already available if the batch UI is later collapsed from per-root fan-out into a single request.
- Additional project documentation for development process, Agile Scrum methodology, backend/UI architecture, and Docker orchestration is available in `docs/development-process-and-architecture.md`.

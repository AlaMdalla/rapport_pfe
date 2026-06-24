# Decision Module - Technical Specification

## 1. Purpose
Expose a lightweight NestJS aggregation endpoint that transforms already-collected work item and repository tag context into decision-oriented buckets for downstream consumers.

---

## 2. Architecture Overview

```
decision.controller.ts
   -> decision-aggregate.service.ts

decision-aggregate.service.ts
   -> DecisionInputSetDto
   -> DecisionAggregateResultDto
   -> RepoBeforeAfterDto
   -> CommitResultDto
```

### Mermaid Architecture Diagram

::: mermaid
flowchart TD
  C[DecisionController] --> S[DecisionAggregateService]
  S --> IN[DecisionInputSetDto]
  S --> OUT[DecisionAggregateResultDto]
  S --> RB[RepoBeforeAfterDto]
  S --> CR[CommitResultDto]
:::

### Mermaid Class Diagram

::: mermaid
classDiagram
  class DecisionController {
    +aggregate(input)
  }
  class DecisionAggregateService {
    +aggregate(input)
    -isDone(workItem)
  }
  class DecisionInputSetDto
  class DecisionAggregateResultDto
  class RepoBeforeAfterDto
  class CommitResultDto

  DecisionController --> DecisionAggregateService
  DecisionAggregateService --> DecisionInputSetDto
  DecisionAggregateService --> DecisionAggregateResultDto
  DecisionAggregateService --> RepoBeforeAfterDto
  DecisionAggregateService --> CommitResultDto
:::

Key points:
- `DecisionController` defines the HTTP contract for the aggregation endpoint.
- `DecisionAggregateService` contains the full classification logic; the module has no external service dependencies besides logging.
- The implementation is synchronous and deterministic because it only transforms the supplied request body.

---

## 3. File Layout

| File | Responsibility |
|------|----------------|
| `src/decision/decision.controller.ts` | HTTP route under `/decision` |
| `src/decision/decision.module.ts` | Registers controller and service |
| `src/decision/service/decision-aggregate.service.ts` | Core aggregation and classification logic |
| `src/decision/dto/decision-input-set.dto.ts` | Root request DTO |
| `src/decision/dto/decision-input-work-item.dto.ts` | Work item input DTO |
| `src/decision/dto/repo-reference-with-name.dto.ts` | Repository input DTO |
| `src/decision/dto/commit-input.dto.ts` | Commit input DTO with tag context |
| `src/decision/dto/decision-aggregate-result.dto.ts` | Root response DTO |
| `src/decision/dto/repo-before-after.dto.ts` | Repository result bucket DTO |
| `src/decision/dto/commit-result.dto.ts` | Commit result DTO with optional `considerForPR` |

---

## 4. Implemented Endpoint

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/decision/aggregate` | Aggregates work items and repository commit tag context |

Controller-level exception handling uses `@UseFilters(MesGenericErrorFilter)`.

---

## 5. Service Internals

### 5.1 DecisionController
- Accepts `DecisionInputSetDto` in the request body.
- Logs input sizes before delegation.
- Delegates processing entirely to `DecisionAggregateService.aggregate(...)`.
- Returns `DecisionAggregateResultDto`.

### 5.2 DecisionAggregateService
- Uses a local static helper `isDone(...)` to normalize work item state checks.
- Steps:
  1. Partition `input.workItems` into `doneWorkItems` and `otherWorkItems`.
  2. Iterate over each repository from `input.repositories`.
  3. Precompute `repoHasAfter` by checking whether any commit has `tagAfter` or `exactTags`.
  4. For each commit, compute:
     - `hasBefore = tagBefore.length > 0`
     - `hasAfter = tagAfter.length > 0 || exactTags.length > 0`
  5. Build `CommitResultDto` objects and push them into one of three per-repository arrays:
     - `beforeAndAfterCommits`
     - `onlyBeforeCommits`
     - `onlyAfterCommits`
  6. When a commit lands in `onlyBeforeCommits` and `repoHasAfter` is true, set `considerForPR = true`.
  7. Emit a `RepoBeforeAfterDto` into the corresponding top-level result array only when the per-repository array is non-empty.
  8. Convert the final plain object into `DecisionAggregateResultDto` via `plainToInstance(...)`.

---

## 6. DTOs and Response Contracts

Main DTOs (`src/decision/dto/`):
- `DecisionInputSetDto`:
  - `workItems: DecisionInputWorkItemDto[]`
  - `repositories: RepoReferenceWithNameDto[]`
- `DecisionInputWorkItemDto`:
  - `id: number`
  - `state?: string | null`
- `RepoReferenceWithNameDto`:
  - `repositoryName: string`
  - `commits: CommitInputDto[]`
- `CommitInputDto`:
  - `commitId: string`
  - `tagBefore: string[]`
  - `tagAfter: string[]`
  - `exactTags: string[]`
- `DecisionAggregateResultDto`:
  - `doneWorkItems: DecisionInputWorkItemDto[]`
  - `otherWorkItems: DecisionInputWorkItemDto[]`
  - `reposWithBeforeAndAfter: RepoBeforeAfterDto[]`
  - `reposWithOnlyBefore: RepoBeforeAfterDto[]`
  - `reposWithOnlyAfter: RepoBeforeAfterDto[]`
- `RepoBeforeAfterDto`:
  - `repositoryName: string`
  - `commits: CommitResultDto[]`
- `CommitResultDto`:
  - `commitId: string`
  - `tagBefore: string[]`
  - `tagAfter: string[]`
  - `exactTags: string[]`
  - `considerForPR?: boolean`

Validation details:
- Request DTOs use `class-validator` and `class-transformer` for nested array validation.
- `repositoryName` must be a non-empty string.
- Work item `state` is optional.
- Tag arrays are required on every commit input.

---

## 7. Error Handling and Logging

- Controller layer is guarded by `MesGenericErrorFilter`.
- `DecisionController` logs request and result sizes with structured context.
- `DecisionAggregateService` wraps aggregation in `try/catch`.
- Unexpected failures are logged via `AppLogger.error(...)` and rethrown as `InternalServerErrorException('Failed to aggregate decision input')`.
- Because the service performs only in-memory transformation, most expected failures are validation-related and occur before service execution.

---

## 8. Performance Characteristics

- Aggregation is in-memory and single-pass per repository.
- Work item partitioning uses simple array filters.
- Repository classification is linear relative to the total number of commits supplied in the payload.
- No outbound network calls, persistence operations, or concurrency controls are involved in this module.

---

## 9. Known Technical Notes

- The module assumes upstream services have already computed commit tag context correctly.
- `exactTags` are treated as `after` evidence for classification purposes.
- Commits with no `tagBefore`, `tagAfter`, or `exactTags` are silently ignored in repository output buckets.
- The endpoint currently returns input work item objects directly in the result, without additional enrichment.

---

## 10. Future Improvements

- Add unit tests covering each commit classification branch and `considerForPR` behavior.
- Add optional summary counts per bucket to simplify UI consumption.
- Clarify or externalize the business rule that maps `exactTags` onto the `after` side.
- Consider adding OpenAPI examples for the aggregate request and response payloads.
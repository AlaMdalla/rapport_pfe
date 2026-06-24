# Decision Module - Functional Specification

## 1. Module Overview

**Module name:** Decision Module

**Purpose:** Provide a decision-support aggregation endpoint that classifies work items and repository commits based on work item status and tag-position information already resolved upstream.

**Description:** The module exposes a single endpoint under `/decision`, accepts a set of work items and repository commit tag contexts, and returns grouped results that help downstream consumers identify completed work items and repository commits that fall before, after, or across release-tag boundaries.

---

## 2. Functional Scope

### Included in current implementation
- Aggregate work items by status (`done` vs non-`done`)
- Aggregate repository commits into three buckets:
  - commits with both a tag before and a tag after/exact tag
  - commits with only a tag before
  - commits with only a tag after or exact tag
- Mark `only before` commits with `considerForPR: true` when the same repository also contains at least one commit with an after/exact tag
- Preserve repository grouping in the response

### Not implemented in current module
- Retrieval of work items, commits, or tags from Azure DevOps
- Persistence of aggregation results
- Workflow execution, approval, or decision state transitions
- Authentication/authorization policy management (handled upstream)
- Validation of business meaning for tag names beyond structural presence/absence

---

## 3. API Endpoint

### 3.1 `POST /decision/aggregate`
- **Request body:** `DecisionInputSetDto`
  - `workItems[]`
    - `id` (required number)
    - `state` (optional string or null)
  - `repositories[]`
    - `repositoryName` (required non-empty string)
    - `commits[]`
      - `commitId` (required string)
      - `tagBefore` (required string array)
      - `tagAfter` (required string array)
      - `exactTags` (required string array)
- **Behavior:**
  1. Split input work items into `doneWorkItems` and `otherWorkItems`.
  2. For each repository, inspect every commit's `tagBefore`, `tagAfter`, and `exactTags` arrays.
  3. Place each commit into one of three repository-level buckets:
     - `reposWithBeforeAndAfter`
     - `reposWithOnlyBefore`
     - `reposWithOnlyAfter`
  4. For `only before` commits, set `considerForPR: true` if the repository contains at least one commit with `tagAfter` or `exactTags`.
  5. Return only non-empty repository groups in each bucket.
- **Response shape:**
  - `doneWorkItems[]`
  - `otherWorkItems[]`
  - `reposWithBeforeAndAfter[]`
  - `reposWithOnlyBefore[]`
  - `reposWithOnlyAfter[]`

---

## 4. Behavioral Rules

- A work item is considered `done` when `state`, lowercased, equals `done`.
- Missing or null `state` values are treated as non-`done`.
- A commit is considered to have a `before` state when `tagBefore.length > 0`.
- A commit is considered to have an `after` state when `tagAfter.length > 0` or `exactTags.length > 0`.
- `exactTags` are functionally treated as part of the `after` side for aggregation.
- Commits that have neither `before` nor `after` information are ignored and do not appear in any repository result bucket.
- Repositories are included in a response bucket only if that bucket contains at least one classified commit.
- The endpoint is read-only with respect to external systems; it only transforms the submitted payload.

---

## 5. Data Models

### DecisionInputWorkItem
```typescript
{
  id: number,
  state?: string | null
}
```

### CommitInput
```typescript
{
  commitId: string,
  tagBefore: string[],
  tagAfter: string[],
  exactTags: string[]
}
```

### Repository input
```typescript
{
  repositoryName: string,
  commits: CommitInput[]
}
```

### CommitResult
```typescript
{
  commitId: string,
  tagBefore: string[],
  tagAfter: string[],
  exactTags: string[],
  considerForPR?: boolean
}
```

### Repository result
```typescript
{
  repositoryName: string,
  commits: CommitResult[]
}
```

### Aggregate response
```typescript
{
  doneWorkItems: DecisionInputWorkItem[],
  otherWorkItems: DecisionInputWorkItem[],
  reposWithBeforeAndAfter: RepositoryResult[],
  reposWithOnlyBefore: RepositoryResult[],
  reposWithOnlyAfter: RepositoryResult[]
}
```

---

## 6. Success Criteria

- The endpoint returns deterministic classifications for the same input payload.
- Work items are correctly partitioned based on `state === 'done'` (case-insensitive).
- Repository commit results preserve repository names and commit tag context.
- `only before` commits are flagged with `considerForPR` only when the repository also contains `after`/`exact` evidence.
- Empty repositories are not emitted into unrelated result buckets.
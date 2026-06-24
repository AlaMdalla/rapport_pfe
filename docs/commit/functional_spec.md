# Commit Module - Functional Specification

## 1. Module Overview

**Module name:** Commit Module

**Purpose:** Provide read-only APIs to retrieve commit data linked to work items, pull requests, repository branches, and tags in Azure DevOps.

**Description:** The module exposes endpoints under `/commits`, parses route/query inputs in the controller layer, and delegates commit retrieval logic to dedicated services for PR, work item, and history/tag resolution use cases.

---

## 2. Functional Scope

### Included in current implementation
- Get commits linked to a work item: `GET /commits/workitems/:workItemId`
- Get commits linked to a pull request: `GET /commits/pullrequests/:prId`
- List repository branches and tags: `GET /commits/branches`
- Get branches and tags related to a commit: `GET /commits/tags`
- Batch resolve tags for multiple commits: `GET /commits/tags/batch`

### Not implemented in current module
- Creating/updating/deleting commits, branches, or tags
- Repository lifecycle operations
- File diff/content retrieval for commits
- Real-time streaming for commit events
- Authentication/authorization policy management (handled upstream)

---

## 3. API Endpoints

### 3.1 `GET /commits/workitems/:workItemId`
- **Path params:** `workItemId` (required numeric string)
- **Query params:** `project` (optional string)
- **Behavior:**
  1. Parse `workItemId` to number.
  2. Resolve commits from direct work item links and related pull requests.
  3. Return deduplicated commit list.
- **Response shape:**
  - `success: true`
  - `data.workItemId`
  - `data.project`
  - `data.commitCount`
  - `data.commits[]` (`commitId`, `repoName`)

### 3.2 `GET /commits/pullrequests/:prId`
- **Path params:** `prId` (required numeric string)
- **Query params:** `project` (optional string)
- **Behavior:**
  1. Parse `prId` to number.
  2. Resolve repository by pull request.
  3. Fetch pull request commits and deduplicate by `commitId`.
- **Response shape:**
  - `success: true`
  - `data.prId`
  - `data.project`
  - `data.commitCount`
  - `data.commits[]` (`commitId`, `repoName`)

### 3.3 `GET /commits/branches`
- **Query params:**
  - `project` (required string)
  - `repositoryName` (required string)
- **Behavior:**
  1. Find repository by name.
  2. Read refs.
  3. Split refs into branch and tag arrays.
- **Response shape:**
  - Success:
    - `success: true`
    - `branches: string[]`
    - `tags: string[]`
  - Failure (example: repository not found):
    - `success: false`
    - `message: string`
    - `branches: []`
    - `tags: []`

### 3.4 `GET /commits/tags`
- **Query params:**
  - `commitId` (required string)
  - `project` (required string)
  - `repositoryName` (required string)
- **Behavior:**
  1. Resolve repository.
  2. Resolve tag refs and tag relations for the target commit.
  3. Return exact tag matches, or nearest surrounding tags when exact match is absent.
  4. Only when no tags are found, resolve branch refs containing the target commit.
- **Response shape:**
  - Success:
    - `success: true`
    - `branches: string[]`
    - `tags: string[]`
  - Failure (examples: repository not found, commit not found, resolution failure):
    - `success: false`
    - `message: string`
    - `branches: []`
    - `tags: []`

### 3.5 `GET /commits/tags/batch`
- **Query params:**
  - `project` (required string)
  - `repositoryName` (required string)
  - `commitIds` (required comma-separated string, max 100 IDs)
- **Behavior:**
  1. Validate `commitIds` is non-empty and does not exceed 100 entries.
  2. Resolve repository and all resolvable tag references.
  3. Choose the latest resolved tag by tag date.
  4. Find branches containing that latest tag commit and select one branch deterministically.
  5. Scan only the selected branch history and resolve per-commit context (`exactTags`, `tagAfter`, `tagBefore`, `foundInBranch`).
- **Response shape:**
  - Success:
    - `success: true`
    - `results: Record<string, { exactTags: string[]; tagAfter: string[]; tagBefore: string[]; foundInBranch: boolean }>`
  - Failure:
    - `success: false`
    - `message: string`
    - `results: {}`

---

## 4. Behavioral Rules

- Controller parses numeric route IDs before delegating to services.
- Missing repository or commit resolution in history/tag operations returns `success: false` with a message.
- Work item and PR commit responses are deduplicated by commit hash.
- Work item commit expansion is resilient: one PR expansion failure is logged and skipped without failing the full response.
- Tag resolution supports both lightweight and annotated tags.
- In tags-by-commit flow, branch resolution is fallback-only and runs only if no tags were resolved.
- Batch tags flow rejects requests above 100 commit IDs.
- Batch tags branch selection is deterministic and lexicographical among matching branch refs.

---

## 5. Data Models

### CommitInfo
```typescript
{
  commitId: string,
  repoName: string
}
```

### CommitsByPR response envelope
```typescript
{
  success: true,
  data: {
    prId: number,
    project: string,
    commitCount: number,
    commits: CommitInfo[]
  }
}
```

### CommitsByWorkItem response envelope
```typescript
{
  success: true,
  data: {
    workItemId: number,
    project: string,
    commitCount: number,
    commits: CommitInfo[]
  }
}
```

### Repository references response envelope
```typescript
{
  success: boolean,
  message?: string,
  branches: string[],
  tags: string[]
}
```

### Batch tags response envelope
```typescript
{
  success: boolean,
  message?: string,
  results: Record<string, {
    exactTags: string[],
    tagAfter: string[],
    tagBefore: string[],
    foundInBranch: boolean
  }>
}
```

---

## 6. Success Criteria

- Endpoints return stable DTO-aligned schemas for downstream consumers.
- Duplicate commits are not returned in PR/work item commit lists.
- Branch/tag listing calls remain read-only and deterministic.
- Tag matching logic can return exact and nearest surrounding tags for commit traceability.
- Batch tag resolution remains bounded to 100 commits per call and returns deterministic results.

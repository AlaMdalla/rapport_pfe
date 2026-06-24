# Commit Tags Endpoint - Current Logic, Step by Step

## Scope

This document explains the current runtime flow for:

- HTTP endpoint: `GET /commits/tags`
- Controller entry: `CommitController.getTagsByCommit`
- Final response: `RepoReferencesResponseDto`

It reflects the current implementation:

The important change from older documentation is this:

- single-commit resolution scans every containing branch history separately
- batch resolution does not do that; it uses one selected branch based on the latest resolved tag
- tag resolution supports both annotated tags and lightweight tags
- ref matching uses the fallback history scan because commit filtering is not available in the current Azure DevOps SDK used here

---

## 1. Public Endpoints

File: `src/commit/commit.controller.ts`

### Single commit endpoint

Route:

- `GET /commits/tags`
- controller method: `getTagsByCommit(...)`
- response type: `RepoReferencesResponseDto`

Swagger summary:

> Get exact or surrounding tags for a commit; if none are found, return containing branches

The controller binds the query to `CommitTagsQueryDto` and forwards it unchanged to the service:

```ts
return this.commitService.getBranchesAndTagsByCommit(
  query.project,
  query.repositoryName,
  query.commitId,
);
```

### Batch endpoint

Route:

- `GET /commits/tags/batch`
- controller method: `getTagsByCommitBatch(...)`
- response type: `BatchTagsResponseDto`

Swagger summary:

> Batch resolve exact or surrounding tags for multiple commits using only the latest tag branch history

The controller binds the query to `CommitTagsBatchQueryDto` and forwards it unchanged:

```ts
return this.commitService.getBranchesAndTagsByCommitBatch(
  query.project,
  query.repositoryName,
  query.commitIds,
);
```

---

## 2. Query DTOs

### `CommitTagsQueryDto`

Used by `GET /commits/tags`.

```ts
export class CommitTagsQueryDto {
  @IsString()
  @IsNotEmpty()
  public commitId!: string;

  @IsString()
  @IsNotEmpty()
  public project!: string;

  @IsString()
  @IsNotEmpty()
  public repositoryName!: string;
}
```

Example request:

```http
GET /commits/tags?project=MES_X.0&repositoryName=mes-platform-api&commitId=abc123
```

### `CommitTagsBatchQueryDto`

Used by `GET /commits/tags/batch`.

Important behavior:

- `commitIds` may arrive as a comma-separated string
- the DTO transforms that string into `string[]`
- empty entries are removed
- validation enforces a non-empty array with a maximum of 100 commit IDs

Example request:

```http
GET /commits/tags/batch?project=MES_X.0&repositoryName=mes-platform-api&commitIds=c1,c2,c3
```

Example transformed value:

```ts
query.commitIds = ['c1', 'c2', 'c3'];
```

---

## 3. Service Delegation Layer

File: `src/commit/service/commit.service.ts`

`CommitService` is still only a facade for these flows.

### Single commit

`getBranchesAndTagsByCommit(...)`:

- delegates to `CommitHistoryService.getBranchesAndTagsByCommit(...)`
- logs on failure
- rethrows the error

### Batch

`getBranchesAndTagsByCommitBatch(...)`:

- delegates to `CommitHistoryService.getBranchesAndTagsByCommitBatch(...)`
- logs on failure
- rethrows the error

The payload shape is determined entirely in `CommitHistoryService`.

---

## 4. Shared Helper Functions

Files:

- `src/commit/utils/tag-resolution.utils.ts`
- `src/commit/utils/tag-selection.utils.ts`
- `src/commit/utils/commit-reference.utils.ts`

The runtime behavior depends on these helpers.

### Repository resolution

`findRepositoryId(...)`:

- loads repositories for the project
- matches by repository display name
- returns `undefined` instead of throwing when it cannot resolve the repository

### Commit validation

`getTargetCommitInfo(...)`:

- calls `gitApi.getCommit(...)`
- returns `{ found: true }` when the commit exists
- returns `{ found: false, errorMessage }` when the commit is not found or the call fails

### Tag resolution

`resolveTagReferences(...)` resolves all tag refs into this shape:

```ts
interface ResolvedTag {
  name: string;
  tagCommitId: string;
  tagDateMs?: number;
}
```

`resolveTagCommit(...)` supports both cases:

- annotated tags via `getAnnotatedTag(...)`
- lightweight tags via `getCommit(...)` fallback

### Commit-to-tag map

`buildCommitToTagMap(...)` returns:

```ts
Map<string, Array<string>>
```

This preserves all tag names that resolve to the same commit.

Example:

```ts
new Map([
  ['c4', ['refs/tags/v4']],
  ['c2', ['refs/tags/v2', 'refs/tags/v2-hotfix']],
]);
```

### Surrounding tag scan

`findSurroundingTagsForCommit(...)` scans one linear history from newest to oldest and returns:

```ts
interface SurroundingTags {
  tagAfter: Array<string>;
  tagBefore: Array<string>;
}
```

Meaning:

- `tagAfter`: the most recent tag seen at or above the target commit in the scanned history
- `tagBefore`: the next tagged commit encountered below the target commit

### Ref matching

`findMatchingReferenceNames(...)` currently uses the fallback history scan because commit filtering through `getRefs(...)` is not available in the SDK version used by this service.

That means the current matching strategy is:

- inspect candidate refs
- fetch history page by page from each ref tip
- return the refs whose history contains the target commit

The helper comment explicitly describes this as fallback behavior.

---

## 5. Single Commit Flow: `GET /commits/tags`

Core method:

```ts
CommitHistoryService.getBranchesAndTagsByCommit(
  project,
  repositoryName,
  commitId,
)
```

This is the current runtime order.

### Step 1: Resolve repository

The service gets the Git API client and resolves the repository ID.

If the repository cannot be found, it returns early:

```json
{
  "success": false,
  "message": "Repository \"mes-platform-api\" not found in project \"MES_X.0\"",
  "branches": [],
  "tags": []
}
```

### Step 2: Load refs and validate the target commit

The service loads all refs once using `gitApi.getRefs(...)`.

Then it validates the target commit with `getTargetCommitInfo(...)`.

If the commit does not exist, it returns early:

```json
{
  "success": false,
  "message": "Commit \"abc123\" not found in repository \"mes-platform-api\"",
  "branches": [],
  "tags": []
}
```

### Step 3: Resolve all tags to commit SHAs

The service filters `refs/tags/*` and resolves each tag to the commit it points to.

Example:

```ts
resolvedTags = [
  { name: 'refs/tags/v4', tagCommitId: 'c4' },
  { name: 'refs/tags/v2', tagCommitId: 'c2' },
  { name: 'refs/tags/v2-hotfix', tagCommitId: 'c2' },
];
```

### Step 4: Return exact tags immediately when available

The service builds `commitToTagMap` and checks the target commit directly:

```ts
const exactTagNames = commitToTagMap.get(commitId) ?? [];
```

If any exact tags are found:

- they are deduplicated
- `refs/tags/` is removed
- the method returns immediately
- branch scanning is skipped completely

Example response:

```json
{
  "success": true,
  "branches": [],
  "tags": ["v2", "v2-hotfix"]
}
```

### Step 5: Find containing branches

If there is no exact tag, the service checks branch refs only.

It calls:

```ts
findMatchingReferenceNames(
  gitApi,
  repositoryId,
  project,
  branchReferences,
  commitId,
  async (reference) => reference.objectId,
  logger,
)
```

Example result:

```ts
branchNames = ['refs/heads/release/1.0'];
```

Normalized branch names used for fallback responses:

```ts
branches = ['release/1.0'];
```

### Step 6: Scan each containing branch history independently

This is the current behavior that matters most.

For every matching branch ref, the service fetches the branch history from that branch tip:

```ts
fetchCommitHistoryFromReference(
  gitApi,
  repositoryId,
  project,
  reference.objectId,
  reference.name ?? 'unknown-branch',
  logger,
)
```

Example history:

```ts
branchHistory = [
  { commitId: 'c5' },
  { commitId: 'c4' },
  { commitId: 'c3' },
  { commitId: 'c2' },
];
```

This avoids assuming that one global history is valid across multiple branches.

### Step 7: Collect surrounding tags from each matching branch

For each branch history, the service calls `findSurroundingTagsForCommit(...)`.

Example:

```ts
commitToTagMap = new Map([
  ['c4', ['refs/tags/v4']],
  ['c2', ['refs/tags/v2']],
]);

branchHistory = [
  { commitId: 'c5' },
  { commitId: 'c4' },
  { commitId: 'c3' },
  { commitId: 'c2' },
];
```

For target `c3`:

```ts
{
  tagAfter: ['refs/tags/v4'],
  tagBefore: ['refs/tags/v2'],
}
```

The service then:

- combines all `tagAfter` and `tagBefore` values from all matching branches
- flattens them
- deduplicates them
- strips `refs/tags/`

Example success response:

```json
{
  "success": true,
  "branches": [],
  "tags": ["v4", "v2"]
}
```

### Step 8: Fallback to containing branches

If no exact tags and no surrounding tags are found, the service returns branch matches only:

```json
{
  "success": true,
  "branches": ["release/1.0"],
  "tags": []
}
```

Priority order for the single endpoint is:

1. exact tags
2. surrounding tags across containing branches
3. containing branches

---

## 6. Batch Flow: `GET /commits/tags/batch`

Core method:

```ts
CommitHistoryService.getBranchesAndTagsByCommitBatch(
  project,
  repositoryName,
  commitIds,
)
```

This path is intentionally different from the single-commit endpoint.

### Step 1: Validate batch size

The method returns failure DTOs when:

- `commitIds.length === 0`
- `commitIds.length > 100`

Examples:

```json
{
  "success": false,
  "message": "commitIds array cannot be empty",
  "results": {}
}
```

```json
{
  "success": false,
  "message": "Maximum 100 commits per batch request",
  "results": {}
}
```

### Step 2: Resolve repository and tags

The method:

- resolves the repository ID
- loads all refs
- resolves all tag refs

If no resolvable tags exist at all, it returns:

```json
{
  "success": false,
  "message": "No resolvable tags found in repository \"mes-platform-api\"",
  "results": {}
}
```

### Step 3: Select a single branch from the latest resolved tag

The batch strategy does not scan every containing branch for every commit.

Instead it:

- sorts resolved tags by `tagDateMs` descending
- picks the latest tag
- finds branches containing that latest tag commit
- chooses one branch with `pickBranchRef(...)`

`pickBranchRef(...)` selection rule is:

1. lexicographically first matching branch name

If no branch contains the latest tag commit, the batch call fails.

### Step 4: Fetch one branch history

The service loads commit history only from the selected branch tip.

That single history is then used for all requested commit IDs in the batch.

This is a performance and strategy tradeoff, and it is different from the single endpoint.

### Step 5: Resolve per-commit tag context

For each requested `commitId`:

- `findSurroundingTagsForCommit(...)` is run against the selected branch history
- exact tags are loaded from `commitToTagMap`
- `foundInBranch` is set based on whether the target commit exists in the scanned branch history
- `tagAfter` excludes exact tags when the commit is directly tagged

Current per-commit shape:

```ts
{
  exactTags: string[];
  tagAfter: string[];
  tagBefore: string[];
  foundInBranch: boolean;
}
```

If a commit is not present in the selected branch history:

```json
{
  "exactTags": [],
  "foundInBranch": false,
  "tagAfter": [],
  "tagBefore": []
}
```

### Step 6: Return `BatchTagsResponseDto`

The batch response is a map keyed by commit SHA:

```json
{
  "success": true,
  "results": {
    "c1": {
      "exactTags": ["v1"],
      "foundInBranch": true,
      "tagAfter": [],
      "tagBefore": ["v0"]
    },
    "c2": {
      "exactTags": [],
      "foundInBranch": true,
      "tagAfter": ["v4"],
      "tagBefore": ["v2"]
    },
    "c3": {
      "exactTags": [],
      "foundInBranch": false,
      "tagAfter": [],
      "tagBefore": []
    }
  }
}
```

---

## 7. Response DTOs

### `RepoReferencesResponseDto`

Used by the single endpoint and by `getRepoBranchesAndTags(...)`.

Shape:

```ts
{
  branches: string[];
  tags: string[];
  success: boolean;
  message?: string;
}
```

### `BatchTagsResponseDto`

Used by the batch endpoint.

Shape:

```ts
{
  results: Record<string, {
    exactTags: string[];
    tagAfter: string[];
    tagBefore: string[];
    foundInBranch: boolean;
  }>;
  success: boolean;
  message?: string;
}
```

---

## 8. Practical Summary

Current behavior, in one view:

- `/commits/tags` is the more accurate branch-aware path for one commit because it scans every containing branch independently
- `/commits/tags/batch` is the faster bulk path because it scans only one selected branch based on the latest resolved tag
- exact tags always win over surrounding-tag lookup
- surrounding tags are based on linear newest-to-oldest history scans
- branch membership checks currently rely on fallback history scans, not server-side ref filtering in the SDK

If this document and runtime behavior ever diverge, `CommitHistoryService` and the helper functions under `src/commit/utils` are the source of truth.

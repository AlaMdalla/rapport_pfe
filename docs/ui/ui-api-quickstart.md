# UI Quickstart: Work Item APIs

This guide gives frontend context to consume work item, related work item, and commit tag endpoints:

- `GET /workitem/tasks/stream` - Stream task work items progressively via SSE
- `GET /workitem/:id` - Get a single work item by ID
- `GET /workitem/:id/related` - Get related work items for a single root ID
- `GET /workitem/related` - Get related work items for multiple root IDs (batch)
- `GET /commits/tags` - Get tags for a single commit
- `GET /commits/tags/batch` - Get tags for multiple commits

---

## Stream Tasks (SSE)

The endpoint streams task data using Server-Sent Events (SSE).

### Endpoint

- Method: `GET`
- Path: `/workitem/tasks/stream`
- Type: `text/event-stream`
- Auth: no custom header contract is defined in this endpoint

Backend note:

- The backend currently uses a fixed project (`MES_X.0`) internally for this stream.
- The UI does not send a project query param for this endpoint.

## Base URL

Use your UI env base URL plus path:

- Example full URL: `${API_BASE_URL}/workitem/tasks/stream`

If your environment already has a path prefix in the base (for example `/job-be`), do not duplicate it in code.

## SSE Message Contract

The backend writes JSON payloads in `data:` frames.

### Batch message

Sent multiple times while loading:

```json
{
	"batch": [
		{
			"id": 123,
			"fields": {
				"System.Title": "Task title"
			}
		}
	],
	"batchNumber": 1,
	"totalLoaded": 200
}
```

Use this to progressively render rows.

### Complete message

Sent once when loading is finished:

```json
{
	"complete": true,
	"totalTasks": 834,
	"batchesProcessed": 5
}
```

After this, the backend closes the connection.

### Error message

Sent when stream processing fails:

```json
{
	"error": "Error message"
}
```

After this, the backend closes the connection.

## Vue 3 Client Example (TypeScript)

Use native `EventSource` when no custom auth header is required.

```ts
type TaskBatchMessage = {
	batch: Array<Record<string, unknown>>;
	batchNumber: number;
	totalLoaded: number;
};

type TaskCompleteMessage = {
	complete: true;
	totalTasks: number;
	batchesProcessed: number;
};

type TaskErrorMessage = {
	error: string;
};

type TaskStreamMessage =
	| TaskBatchMessage
	| TaskCompleteMessage
	| TaskErrorMessage;

export function openTaskStream(
	apiBaseUrl: string,
	onBatch: (message: TaskBatchMessage) => void,
	onComplete: (message: TaskCompleteMessage) => void,
	onError: (message: TaskErrorMessage | Error) => void,
): () => void {
	const source = new EventSource(`${apiBaseUrl}/workitem/tasks/stream`);

	source.onmessage = (event: MessageEvent<string>) => {
		try {
			const payload = JSON.parse(event.data) as TaskStreamMessage;

			if ('error' in payload) {
				onError(payload);
				source.close();
				return;
			}

			if ('complete' in payload && payload.complete) {
				onComplete(payload);
				source.close();
				return;
			}

			if ('batch' in payload) {
				onBatch(payload);
			}
		} catch {
			onError(new Error('Invalid SSE payload received from task stream'));
			source.close();
		}
	};

	source.onerror = () => {
		onError(new Error('Task stream connection error'));
		source.close();
	};

	return () => {
		source.close();
	};
}
```

## Recommended UI State Model

- `tasks`: accumulated list
- `totalLoaded`: number
- `isStreaming`: boolean
- `isComplete`: boolean
- `batchesProcessed`: number
- `errorMessage`: string | null

On each batch:

- append or merge `batch` into `tasks`
- update `totalLoaded`

On complete:

- set `isComplete = true`
- set `isStreaming = false`

On error:

- set `errorMessage`
- set `isStreaming = false`

## CORS Notes

Backend CORS currently allows:

- `http://localhost:5173`
- `https://mesx-dev.app.corp`

If your UI host differs, backend CORS must be updated.

## Quick Manual Test

Use browser devtools console:

```js
const es = new EventSource('http://localhost:3000/workitem/tasks/stream');
es.onmessage = (e) => console.log('SSE', JSON.parse(e.data));
es.onerror = (e) => {
	console.error('SSE error', e);
	es.close();
};
```

---

## Get Single Work Item

Retrieve a single work item by ID with normalized relations (links to other work items and pull requests).

### Endpoint

- Method: `GET`
- Path: `/workitem/:id`
- Type: `application/json`

### Path Params

- `id` (required): Work item ID (numeric)

### Request Examples

```http
GET /workitem/140996
```

### Response DTO

```ts
export interface WorkItemResponseDto {
	success: boolean;
	data: WorkItemDto;
}

export interface WorkItemDto {
	id?: number;
	type?: string | null;
	title?: string | null;
	state?: string | null;
	status?: string | null;
	assignedTo?: string | null;
	links: WorkItemLinkDto[];
}

export interface WorkItemLinkDto {
	type?: string;
	targetId?: string;
	url?: string;
	isPR: boolean;
	prId?: number;
}
```

### Success Response Example

```json
{
	"success": true,
	"data": {
		"id": 140996,
		"type": "Task",
		"title": "[Code Review] [Live Status] GAP mLean widget - Ok First part - detail view & interaction",
		"state": "Active",
		"status": null,
		"assignedTo": "User A",
		"links": [
			{
				"type": "ArtifactLink",
				"targetId": "5001",
				"url": "https://dev.azure.com/.../PullRequestId/5001",
				"isPR": true,
				"prId": 5001
			}
		]
	}
}
```

### Error Response Example

```json
{
	"success": false,
	"message": "Work item not found"
}
```

### Vue TypeScript Client Example

```ts
export async function getWorkItem(
	apiBaseUrl: string,
	workItemId: number,
): Promise<WorkItemResponseDto> {
	const response = await fetch(
		`${apiBaseUrl}/workitem/${workItemId}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
			},
		},
	);

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed: ${response.status}`);
	}

	return (await response.json()) as WorkItemResponseDto;
}
```

---

## Get Related Work Items For Single ID

Use this endpoint to request the full related graph (work items, visited PR ids, and commits) for a single root work item ID.

### Endpoint

- Method: `GET`
- Path: `/workitem/:id/related`
- Type: `application/json`

### Path Params

- `id` (required): Root work item ID (numeric)

### Query Params

- `project` (optional): Azure DevOps project name

### Request Examples

```http
GET /workitem/140996/related?project=MES_X.0
```

### Response DTO

```ts
export interface RelatedWorkItemsResponseDto {
	success: boolean;
	data: RelatedWorkItemsDataDto;
}

export interface RelatedWorkItemsDataDto {
	project: string;
	workItemId: number;
	relatedCount: number;
	workItems: WorkItemDto[];
	visitedPullRequestIds: number[];
	commitCount: number;
	commits: CommitInfoDto[];
}
```

### Success Response Example

```json
{
	"success": true,
	"data": {
		"project": "MES_X.0",
		"workItemId": 140996,
		"relatedCount": 1,
		"workItems": [
			{
				"id": 140996,
				"type": "Task",
				"title": "[Code Review] [Live Status] GAP mLean widget - Ok First part - detail view & interaction",
				"state": "Active",
				"assignedTo": "User A",
				"links": []
			}
		],
		"visitedPullRequestIds": [],
		"commitCount": 0,
		"commits": []
	}
}
```

### Vue TypeScript Client Example

```ts
export async function getRelatedWorkItemsById(
	apiBaseUrl: string,
	workItemId: number,
	project?: string,
): Promise<RelatedWorkItemsResponseDto> {
	const params = new URLSearchParams();
	if (project) {
		params.set('project', project);
	}

	const response = await fetch(
		`${apiBaseUrl}/workitem/${workItemId}/related?${params.toString()}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
			},
		},
	);

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed: ${response.status}`);
	}

	return (await response.json()) as RelatedWorkItemsResponseDto;
}
```

---

## Get Related Work Items For Multiple IDs

Use this endpoint to request the full related graph (work items, visited PR ids, and commits)
for multiple root work item IDs in one call.

### Endpoint

- Method: `GET`
- Path: `/workitem/related`
- Type: `application/json`

### Query Params

- `workItemIds` (required): list of root work item IDs
- `project` (optional): Azure DevOps project name

Notes:

- Maximum `workItemIds` length is 100
- `workItemIds` accepts comma-separated values
- If `project` is omitted, backend uses empty string for internal calls and returns `N/A` in response data

### Request Examples

Comma-separated:

```http
GET /workitem/related?workItemIds=1001,1002,1003&project=MES_X.0
```

Array style (also supported by transform logic):

```http
GET /workitem/related?workItemIds=1001&workItemIds=1002&project=MES_X.0
```

### Response Envelope DTO

```ts
export interface RelatedWorkItemsBatchResponseDto {
	success: boolean;
	data: RelatedWorkItemsBatchDataDto;
}

export interface RelatedWorkItemsBatchDataDto {
	project: string;
	requestedWorkItemIds: number[];
	relatedCount: number;
	workItems: WorkItemDto[];
	visitedPullRequestIds: number[];
	commitCount: number;
	commits: CommitInfoDto[];
}
```

### Nested DTOs Used

```ts
export interface WorkItemDto {
	id?: number;
	type?: string | null;
	title?: string | null;
	state?: string | null;
	status?: string | null;
	assignedTo?: string | null;
	links: WorkItemLinkDto[];
}

export interface WorkItemLinkDto {
	type?: string;
	targetId?: string;
	url?: string;
	isPR: boolean;
	prId?: number;
}

export interface CommitInfoDto {
	commitId: string;
	repoName: string;
}
```

### Success Response Example

```json
{
	"success": true,
	"data": {
		"project": "MES_X.0",
		"requestedWorkItemIds": [1001, 1002],
		"relatedCount": 4,
		"workItems": [
			{
				"id": 1001,
				"type": "Task",
				"title": "Root work item",
				"state": "Active",
				"assignedTo": "User A",
				"links": [
					{
						"type": "ArtifactLink",
						"targetId": "5001",
						"url": "https://dev.azure.com/.../PullRequestId/5001",
						"isPR": true,
						"prId": 5001
					}
				]
			}
		],
		"visitedPullRequestIds": [5001, 5002],
		"commitCount": 3,
		"commits": [
			{
				"commitId": "abc123",
				"repoName": "repo-a"
			}
		]
	}
}
```

### Error Behavior

Typical non-success outcomes:

- `400` for invalid input (for example empty/invalid `workItemIds`)
- `404` when one or more requested root work items are not found
- `500` when Azure DevOps or internal processing fails

Use normal HTTP error handling in UI (`try/catch` around axios/fetch).

### Vue TypeScript Client Example

```ts
export type RelatedQuery = {
	workItemIds: number[];
	project?: string;
};

export async function getRelatedWorkItemsByIds(
	apiBaseUrl: string,
	query: RelatedQuery,
): Promise<RelatedWorkItemsBatchResponseDto> {
	if (!query.workItemIds.length) {
		throw new Error('workItemIds is required');
	}

	const searchParams = new URLSearchParams();
	searchParams.set('workItemIds', query.workItemIds.join(','));
	if (query.project) {
		searchParams.set('project', query.project);
	}

	const response = await fetch(
		`${apiBaseUrl}/workitem/related?${searchParams.toString()}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
			},
		},
	);

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed: ${response.status}`);
	}

	return (await response.json()) as RelatedWorkItemsBatchResponseDto;
}
```

### UI Integration Checklist

- Validate user input ids before calling API
- Send ids as a comma-separated `workItemIds` query param
- Render `data.workItems` as main grid/list
- Show secondary insights from `data.visitedPullRequestIds` and `data.commits`
- Handle `400`/`404`/`500` with clear user-facing messages

---

## Get Tags for a Single Commit

Resolves exact or surrounding tags for a specific commit SHA. If no exact tags are found, returns containing branches.

### Endpoint

- Method: `GET`
- Path: `/commits/tags`
- Type: `application/json`

### Query Params

- `project` (required): Azure DevOps project name
- `repositoryName` (required): Repository name
- `commitId` (required): Commit SHA to search for

### Request Examples

```http
GET /commits/tags?project=MES_X.0&repositoryName=mesx-repo&commitId=abc123def456
```

### Response DTO

```ts
export interface RepoReferencesResponseDto {
	branches: string[];
	tags: string[];
	success: boolean;
	message?: string; // Only present on failure
}
```

### Success Response Example

```json
{
	"success": true,
	"tags": ["v1.2.3", "v1.2.2"],
	"branches": []
}
```

### Fallback Response Example (No Exact Tags)

When no exact tags are found, surrounding branches are returned instead:

```json
{
	"success": true,
	"tags": [],
	"branches": ["main", "develop"]
}
```

### Error Response Example

```json
{
	"success": false,
	"tags": [],
	"branches": [],
	"message": "Commit not found in repository"
}
```

### Vue TypeScript Client Example

```ts
export async function getTagsByCommit(
	apiBaseUrl: string,
	project: string,
	repositoryName: string,
	commitId: string,
): Promise<RepoReferencesResponseDto> {
	const params = new URLSearchParams({
		project,
		repositoryName,
		commitId,
	});

	const response = await fetch(`${apiBaseUrl}/commits/tags?${params.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
		},
	});

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed: ${response.status}`);
	}

	return (await response.json()) as RepoReferencesResponseDto;
}
```

---

## Get Tags for Multiple Commits (Batch)

Batch resolve exact or surrounding tags for multiple commit SHAs using only the latest tag branch history. Returns a map of commitId to tag context for each commit.

### Endpoint

- Method: `GET`
- Path: `/commits/tags/batch`
- Type: `application/json`

### Query Params

- `project` (required): Azure DevOps project name
- `repositoryName` (required): Repository name
- `commitIds` (required): Comma-separated commit SHAs (max 100)

### Request Examples

Comma-separated:

```http
GET /commits/tags/batch?project=MES_X.0&repositoryName=mesx-repo&commitIds=abc123,def456,ghi789
```

Array style (also supported):

```http
GET /commits/tags/batch?project=MES_X.0&repositoryName=mesx-repo&commitIds=abc123&commitIds=def456
```

### Response DTO

```ts
export interface BatchTagsResponseDto {
	results: Record<string, CommitTagContextDto>;
	success: boolean;
	message?: string; // Only present on failure
}

export interface CommitTagContextDto {
	exactTags: string[];      // Tags directly on the commit
	tagAfter: string[];       // Tags after the commit
	tagBefore: string[];      // Tags before the commit
	foundInBranch: boolean;   // Whether commit was found in any branch
}
```

### Success Response Example

```json
{
	"success": true,
	"results": {
		"abc123": {
			"exactTags": ["v1.2.3"],
			"tagAfter": [],
			"tagBefore": ["v1.2.2"],
			"foundInBranch": true
		},
		"def456": {
			"exactTags": [],
			"tagAfter": ["v1.3.0"],
			"tagBefore": ["v1.2.3"],
			"foundInBranch": true
		},
		"ghi789": {
			"exactTags": [],
			"tagAfter": [],
			"tagBefore": [],
			"foundInBranch": false
		}
	}
}
```

### Partial Failure Response Example

```json
{
	"success": false,
	"message": "One or more commits not found",
	"results": {
		"abc123": {
			"exactTags": ["v1.2.3"],
			"tagAfter": [],
			"tagBefore": ["v1.2.2"],
			"foundInBranch": true
		}
	}
}
```

### Vue TypeScript Client Example

```ts
export type BatchTagsQuery = {
	project: string;
	repositoryName: string;
	commitIds: string[];
};

export async function getTagsByCommitBatch(
	apiBaseUrl: string,
	query: BatchTagsQuery,
): Promise<BatchTagsResponseDto> {
	if (!query.commitIds.length) {
		throw new Error('commitIds is required');
	}

	if (query.commitIds.length > 100) {
		throw new Error('Maximum 100 commitIds allowed');
	}

	const params = new URLSearchParams({
		project: query.project,
		repositoryName: query.repositoryName,
		commitIds: query.commitIds.join(','),
	});

	const response = await fetch(
		`${apiBaseUrl}/commits/tags/batch?${params.toString()}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
			},
		},
	);

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed: ${response.status}`);
	}

	return (await response.json()) as BatchTagsResponseDto;
}
```

### UI Integration Checklist

- Validate `commitIds` before calling API (required, max 100)
- Send ids as a comma-separated `commitIds` query param
- For each commit in results, display:
  - `exactTags` as primary tag info
  - `tagBefore` and `tagAfter` for context when exact tags are not found
  - `foundInBranch` status to indicate commit validity
- Handle null/empty tag arrays gracefully (show "N/A" or default indicator)
- Handle `400`/`404`/`500` errors with user-friendly messages
- Consider batch vs single queries based on UI context (single for detail view, batch for table/list operations)

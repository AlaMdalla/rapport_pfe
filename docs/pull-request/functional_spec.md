# Pull Request Module - Functional Specification

## Module Overview

**Module Name:** Pull Request Module

**Purpose:** Provide a single API to retrieve work items linked to a pull request in Azure DevOps.

**Description:** The controller exposes `GET /pullrequests/:prId/workitems`, validates `prId`, delegates to `PullRequestService`, and returns `{ success, data }`.

---

## Functional Scope

### In-Scope (V1)
- Validate PR identifiers supplied via path parameter
- Allow optional project filter via `?project=<name>`
- Fetch PR metadata and work item references from Azure DevOps
- Fetch each referenced work item (with relation expansion)
- Normalize work item payloads (id, title, links)
- Provide consistent JSON response structure for downstream modules

### Out-of-Scope (V1)
- Creating, updating, or deleting pull requests
- Returning PR diffs, reviewers, commits, or policies
- Pagination or filtering beyond `project`
- Streaming responses
- Authentication / authorization logic (handled upstream)

---

## API Endpoints

### GET `/pullrequests/:prId/workitems`
Returns all work items linked to the specified pull request.

**Path Params**
- `prId` (required, number): Azure DevOps pull request ID

**Query Params**
- `project` (optional, string): Azure DevOps project name. Defaults to empty string, allowing the service to pull from configured defaults.

**Response Shape**
```json
{
  "success": true,
  "data": {
    "prId": 102697,
    "project": "MES_X.0",
    "workItemCount": 3,
    "workItems": [
      {
        "id": 134460,
        "title": "Implement feature X",
        "links": [
          {
            "type": "ArtifactLink",
            "prId": 102697,
            "targetId": "vstfs:///Git/Commit/123",
            "url": "https://dev.azure.com/...",
            "isPR": true
          }
        ]
      }
    ]
  }
}
```

**Error Cases**
- `400 Bad Request` if `prId` is missing or non-numeric
- `500 Internal Server Error` when upstream Azure DevOps calls fail unexpectedly

---

## Data Models

### WorkItem
Single work item linked to a pull request.

```typescript
{
  id: number,
  title?: string,
  links: LinkInfo[]
}
```

**Fields:**
- `id` - Azure DevOps work item identifier
- `title` - Work item title (optional, may be absent if fetch failed)
- `links` - Array of relations/links from this work item

### LinkInfo
Normalized relation link metadata.

```typescript
{
  type?: string,
  url?: string,
  targetId?: string,
  isPR: boolean,
  prId?: number
}
```

**Fields:**
- `type` - Relation type (e.g., ArtifactLink, Relates)
- `url` - Absolute URL to the linked resource
- `targetId` - Raw Azure DevOps target identifier
- `isPR` - True if this link points to a pull request
- `prId` - Parsed PR ID (populated when `isPR` is true)

### Response Data
Data envelope structure in API response.

```typescript
{
  prId: number,
  project: string,
  workItemCount: number,
  workItems: WorkItem[]
}
```

**Fields:**
- `prId` - Pull request ID (echo of request path parameter)
- `project` - Project name (from query parameter or default)
- `workItemCount` - Number of work items returned
- `workItems` - Array of work items linked to the PR

### Response Envelope
Complete HTTP response for PR endpoint.

```typescript
{
  success: boolean,
  data: ResponseData
}
```

**Fields:**
- `success` - True on successful execution (including empty results)
- `data` - Response data object containing PR work items

---

## Behavioral Rules
- PR IDs are coerced to numbers; non-finite values are rejected immediately.
- If the PR cannot be resolved to a repository ID, the service returns an empty list.
- If work item references are empty, the service returns an empty list.
- Missing or empty `project` query parameter is allowed; downstream services decide which project to use.
- `success: true` is returned when execution completes normally (including empty results).

---

## Success Criteria
- Responds within Azure DevOps API limits (batch work item fetches executed concurrently).
- Returns stable JSON schema for all consumers.
- Logs validation errors (BadRequest) and backend failures (InternalServerError) for observability.

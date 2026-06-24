# First restitution - demo script

This demo script is designed for a short, clear, and robust restitution. It prioritizes visible functionality and prepares a Swagger fallback if the UI is not available.

---

## 1. Demo objective

Show in a few minutes that the system:

- starts from one or more work items,
- automatically rebuilds the work item -> pull request -> commit -> tag chain,
- consolidates the results,
- and supports decision-making.

---

## 2. Recommended order

1. Quickly show the manual problem.
2. Open the UI and launch a simple trace.
3. Show a batch or sprint scenario.
4. Finish with the aggregated result and decision view.
5. Keep Swagger as a fallback plan.

---

## 3. Spoken introduction for the demo

Suggested sentence:

> Before, we had to navigate manually in Azure DevOps to find linked work items, PRs, commits, and then tags. Now, we will show the same journey through one automated chain.

Visual support:

- [docs/uml/dependency-management-flow-before.puml](../uml/dependency-management-flow-before.puml)
- [docs/uml/dependency-management-flow-after.puml](../uml/dependency-management-flow-after.puml)

---

## 4. Main demo - UI

### Step 1 - Trace one root work item

**UI route**

- `/cnerr-ui/trace/workitem-related`

**What to show**

- entering one root work item,
- displaying related work items,
- visited PRs,
- related commits,
- the structure of the result.

**Spoken message**

> From a single identifier, the system traverses the useful relations and already returns a consolidated view.

**Related backend**

- `GET /workitem/:id/related`
- `GET /pullrequests/:prId/workitems`
- `GET /commits/workitems/:workItemId`

---

### Step 2 - Release context through commits and tags

**What to show**

- retrieved commits,
- branch or tag context,
- release interpretation.

**Spoken message**

> The value is not only to list commits. The value is to know where they stand relative to the release.

**Related backend**

- `GET /commits/tags`
- `GET /commits/tags/batch`
- `GET /commits/branches`

---

### Step 3 - Batch or sprint demo

**Option A - Batch**

- Route: `/cnerr-ui/trace/workitem-batch`
- Show SSE streaming and progress.
- Continue with `/cnerr-ui/trace/workitem-batch-related` for consolidated results.

**Option B - Sprint**

- Route: `/cnerr-ui/trace/sprints`
- Show the sprint list and then the related work items.
- Explain that this allows analysis of a release scope by sprint.

**Related backend**

- `GET /workitem/tasks/stream`
- `GET /workitem/related`
- `GET /sprint/`
- `GET /sprint/:sprintId/work-items`

**Spoken message**

> On larger volumes, we keep the interface responsive thanks to streaming and batch processing.

---

### Step 4 - Decision dashboard

**What to show**

- work item grouping,
- repository grouping,
- a usable view for release decision-making.

**Related backend**

- `POST /decision/aggregate`

**Spoken message**

> The final objective is here: move from artifact collection to a usable decision view.

---

## 5. Plan B - Swagger demo

If the UI is not available, run the same demonstration through Swagger.

**Swagger**

- Backend : `/api`

**Recommended order**

1. `GET /workitem/:id/related`
2. `GET /pullrequests/:prId/workitems`
3. `GET /commits/workitems/:workItemId`
4. `GET /commits/tags/batch`
5. `POST /decision/aggregate`

**Spoken message**

> Even without the interface, we can see that the processing chain is already available and structured at API level.

---

## 6. Likely questions from the expert

### Question - Why a dedicated backend layer instead of calling Azure DevOps directly from the UI?

**Short answer**

To centralize traversal logic, normalize data, secure Azure DevOps access, reduce calls, and keep stable contracts for the UI.

### Question - How do you handle large volumes?

**Short answer**

Batch processing, deduplication, cache, SSE streaming, and grouping calls by repository or by batch.

### Question - Does the system modify Azure DevOps?

**Short answer**

No. All operations are strictly read-only.

### Question - Why DTOs?

**Short answer**

To have a stable internal model, independent from Azure DevOps response variations, and to clearly separate modules.

### Question - What is the final business result?

**Short answer**

A consolidated view that helps the developer or release engineer verify scope, dependencies, and commit position relative to the release.

---

## 7. Points not to forget during the demo

- Always remind the audience of the initial manual problem.
- Do not go too early into code details.
- Show the result first, then explain how it is produced.
- Use diagrams to frame the discussion, not to overload the presentation.
- Keep the LLM part as a bonus if time allows.

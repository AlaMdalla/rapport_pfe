# Backend Class Diagram Description

This file describes the exact DTO class diagram shown in the backend data model view.

## Overview

The diagram is organized into five DTO groups:

- Decision DTOs
- Sprint DTOs
- Work Item DTOs
- Pull Request DTOs
- Commit DTOs

It focuses on the main data structures and their core relationships, not on every response wrapper used by the API.

## Decision DTOs

The decision area is split into input DTOs and aggregation result DTOs.

- `DecisionInputSetDto` is the main input container.
- `DecisionInputSetDto` contains many `DecisionInputWorkItemDto` items through the `workItems` relation.
- `DecisionInputSetDto` contains many `RepoReferenceWithNameDto` items through the `repositories` relation.
- Each `RepoReferenceWithNameDto` can contain many `CommitInputDto` items through the `commits` relation.
- `DecisionAggregateResultDto` is the result container.
- `DecisionAggregateResultDto` connects to many `RepoBeforeAfterDto` items through the `repositoryGroups` relation.
- Each `RepoBeforeAfterDto` can contain many `CommitResultDto` items through the `commits` relation.

## Sprint DTOs

The sprint area is intentionally small.

- `SprintDto` is the main sprint structure.
- `SprintDto` has one `SprintAttributesDto` through the `attributes` relation.
- `SprintWorkItemDto` is shown as a separate DTO used to represent work items linked to a sprint.

## Work Item DTOs

The work item area models recursive dependency traversal results.

- `RelatedWorkItemsDataDto` stores the result for one root work item.
- `RelatedWorkItemsBatchDataDto` stores the result for multiple requested root work items.
- Both result DTOs connect to many `WorkItemDto` items through the `workItems` relation.
- `WorkItemDto` connects to many `WorkItemLinkDto` items through the `links` relation.

## Pull Request DTOs

The pull request area models work items discovered from a pull request.

- `WorkItemsDataDto` is the main container for work items linked to a pull request.
- `WorkItemsDataDto` connects to many `WorkItemResultDto` items through the `workItems` relation.
- `WorkItemResultDto` connects to many `LinkInfoDto` items through the `links` relation.
- `PullRequestSummaryDto` is kept as a compact reference DTO used by the traversal results.

## Commit DTOs

The commit area models commit lookup and version context.

- `CommitsByPRDataDto` connects to many `CommitInfo` items through the `commits` relation.
- `CommitsByWorkItemDataDto` connects to many `CommitInfo` items through the `commits` relation.
- `CommitTagContextDto` is shown as a standalone DTO that stores version lookup context such as exact tags, surrounding tags, and branch presence.

## Cross-Group Relations

The diagram also shows the main cross-group links used by dependency traversal.

- `RelatedWorkItemsDataDto` connects to many `PullRequestSummaryDto` items through `visitedPullRequests`.
- `RelatedWorkItemsBatchDataDto` connects to many `PullRequestSummaryDto` items through `visitedPullRequests`.
- `RelatedWorkItemsDataDto` connects to many `CommitInfo` items through `commits`.
- `RelatedWorkItemsBatchDataDto` connects to many `CommitInfo` items through `commits`.

## Reading Intent

This diagram is meant to be read as a backend data model reference.

- The grouped boxes show the feature area that owns each DTO.
- The arrows show containment or aggregation-style relations.
- The multiplicities show whether a DTO holds a single object or a list of objects.
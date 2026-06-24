Final logical presentation flow:

1. Batch Related WorkItems
- Start from user stories or selected work items.
- Run one batch related analysis to build the consolidated dependency graph.
- Output is the decision-ready work item and commit scope.

2. Commit Tags Fetch
- Use commits discovered in batch analysis.
- Resolve branch and tag context in batch mode.
- Output classifies commit position relative to release tags.

Conclusion:
- This two-part flow is clear, linear, and easy to defend.
- Part 1 explains scope reconstruction.
- Part 2 explains release/version contextualization.
- Together they form the core operational logic before final decision view.

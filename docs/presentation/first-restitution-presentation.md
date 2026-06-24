# First restitution - presentation support

This document is a concise English support for the final-year project presentation. Each slide keeps one main idea, short bullets, a natural speaker explanation, and a clear visual suggestion.

---

## Slide 1 - Opening

**Title**

MES-X Dependency Management  
From manual checks to clear release traceability

**Main idea**

The project turns a long manual analysis into one clear workflow.

**Slide content**

- Dependency analysis is often slow and manual.
- Our system automates this analysis in Azure DevOps.
- It links work items, pull requests, commits, and release tags.
- It gives one clear view instead of many separate screens.

**Speaker explanation**

- This project solves a practical problem in software delivery.
- The goal is to help developers and release engineers understand dependencies faster and with less risk.

**Visual suggestion**

- Keep this slide simple.
- Use the title with a small traceability illustration or a clean icon line.

---

## Slide 2 - Problem

**Title**

Why the current process is difficult

**Main idea**

The data exists, but the analysis is still manual and hard to trust.

**Slide content**

- The user starts from a work item in Azure DevOps.
- They open linked items and related pull requests one by one.
- They then check commits, branches, and tags manually.
- The same navigation is repeated across several screens.
- The final decision depends on manual correlation.

**Speaker explanation**

- The issue is not missing data.
- The issue is that the data is scattered, so the user has to rebuild the full picture manually.

**Visual suggestion**

- Use [docs/uml/dependency-management-flow-before.puml](../uml/dependency-management-flow-before.puml).
- A before-workflow diagram is better than a text-heavy slide here.

---

## Slide 3 - Solution

**Title**

What the solution changes

**Main idea**

The system adds an analysis layer that rebuilds the full traceability chain automatically.

**Slide content**

- Start from one or more work items.
- Traverse related work items automatically.
- Retrieve linked PRs, commits, branches, and tags.
- Normalize the results into stable backend models.
- Show a decision-ready overview in one place.

**Speaker explanation**

- We are not replacing Azure DevOps.
- We are adding a read-only analysis layer that turns scattered information into clear results.

**Visual suggestion**

- Use a simple flow from input to final overview.
- A five-step pipeline works well on this slide.

---

## Slide 4 - Functional flow

**Title**

Main functional flow

**Main idea**

The functional requirements can be explained as one simple end-to-end process.

**Slide content**

- Start from one or more root work items.
- Build the dependency graph automatically.
- Resolve related pull requests and repository context.
- Enrich commits with branch and release tag information.
- Generate one overview to support release decisions.

**Speaker explanation**

- In the report, these functions are grouped by requirement IDs.
- In the presentation, I explain them as one clear user flow from input to decision.

**Visual suggestion**

- Use a horizontal process diagram with 4 or 5 steps.
- Keep the requirement IDs in the report, not on the slide.

---

## Slide 5 - Quality goals

**Title**

Quality requirements behind the solution

**Main idea**

The project is not only about features; it also has to be fast, reliable, and maintainable.

**Slide content**

- Fast enough for real use on large traces.
- Able to scale to more repositories and bigger graphs.
- Reliable even when some external calls fail.
- Easy to maintain with clear modules and APIs.
- Secure and strictly read-only toward Azure DevOps.

**Speaker explanation**

- These quality goals explain many design choices in the project, such as modular services, batch processing, SSE, and documented endpoints.

**Visual suggestion**

- Use five icons or a clean five-column layout.
- Avoid long text on this slide.

---

## Slide 6 - Method

**Title**

How the project was organized

**Main idea**

The work followed a simple Agile rhythm adapted to a technical prototype.

**Slide content**

- Sprint planning around user stories and traceability goals.
- Regular follow-up between backend and UI work.
- Sprint reviews to show working features.
- Retrospectives to simplify diagrams and improve clarity.
- Documentation updated during each increment.

**Speaker explanation**

- Even though this is a prototype, the work was organized in short cycles.
- This helped us improve both the implementation and the presentation quality over time.

**Visual suggestion**

- Use a simple sprint cycle or timeline.
- Keep the visual light and easy to read.

---

## Slide 7 - Architecture

**Title**

System architecture at a glance

**Main idea**

The system is built around a clear separation between UI, backend logic, and Azure DevOps data.

**Slide content**

- The UI lets the user launch trace and decision views.
- The NestJS backend contains the analysis logic.
- The backend retrieves and enriches Azure DevOps data.
- Azure DevOps remains the single source of truth.
- The UI never talks to Azure DevOps directly.

**Speaker explanation**

- All the complex traversal and enrichment logic is centralized in the backend.
- This keeps the frontend simpler and makes the system easier to control.

**Visual suggestion**

- Use [docs/uml/global-architecture.puml](../uml/global-architecture.puml).
- A three-layer diagram is the best fit here.

---

## Slide 8 - Use cases

**Title**

Main user scenarios

**Main idea**

The system is designed around one main goal: help the user understand dependencies and support release decisions.

**Slide content**

- Analyze one work item or a full sprint.
- Explore related work items and pull requests.
- Retrieve commits, branches, and release tags.
- Generate a dependency overview for decision-making.
- Optionally review commits with the LLM module.

**Speaker explanation**

- This slide shows the user journey, not the internal implementation.
- The idea is to show what the user can do from the start of the analysis to the final decision.

**Visual suggestion**

- Use [docs/uml/use-case-model.puml](../uml/use-case-model.puml).
- Keep only the main actor and the most important use cases.

---

## Slide 9 - Data model

**Title**

Normalized backend data model

**Main idea**

The backend uses clear DTO groups so data can move across modules without confusion.

**Slide content**

- Work item DTOs store traversal inputs and results.
- Pull request DTOs connect work tracking to source control.
- Commit DTOs add branch and tag context.
- Sprint DTOs support sprint-based analysis.
- Decision DTOs prepare the final overview.

**Speaker explanation**

- The goal of this diagram is not to show every class.
- It shows how data is organized from the start of the trace to the final decision output.

**Visual suggestion**

- Use [docs/uml/backend-class-diagram.mmd](../uml/backend-class-diagram.mmd).
- Keep only the main DTO groups visible.

---

## Slide 10 - Value

**Title**

Before and after the automation

**Main idea**

This slide shows the business value of the project in the simplest possible way.

**Slide content**

- Before: the user jumps across many Azure DevOps screens.
- Before: the conclusion depends on manual checks.
- After: one starting point launches the full traversal.
- After: the system returns one clear and decision-ready view.

**Speaker explanation**

- This is the key value slide.
- It links the initial pain point directly to the practical result delivered by the project.

**Visual suggestion**

- Use [docs/uml/dependency-management-flow-before.puml](../uml/dependency-management-flow-before.puml) and [docs/uml/dependency-management-flow-after.puml](../uml/dependency-management-flow-after.puml).
- A side-by-side comparison is the most effective format.

---

## Slide 11 - Demo

**Title**

Demo flow

**Main idea**

The demo should be short, simple, and focused on one complete scenario.

**Slide content**

- Start from one root work item.
- Show related work items and visited pull requests.
- Show retrieved commits with branch or tag context.
- Continue with batch mode or sprint mode.
- Finish on the decision dashboard.

**Speaker explanation**

- I will keep the demo focused on one readable scenario.
- The goal is to show the full chain once, without spending too much time on navigation.

**Presenter note**

- Main routes: `/cnerr-ui/trace/workitem-related`, `/cnerr-ui/trace/workitem-batch`, `/cnerr-ui/trace/workitem-batch-related`, `/cnerr-ui/trace/sprints`.
- Detailed script: [docs/presentation/first-restitution-demo-script.md](./first-restitution-demo-script.md)

**Visual suggestion**

- Use 3 or 4 screenshots, or a simple step list with screen names.
- Avoid showing full route paths on the slide itself.

---

## Slide 12 - Results

**Title**

What is already working

**Main idea**

The project already delivers a real working chain, not only a concept.

**Slide content**

- NestJS backend with documented endpoints.
- Recursive retrieval of work items and PR relations.
- Commit resolution from work items and from PRs.
- Branch and tag enrichment, including batch mode.
- UI screens for trace, sprint, and decision views.
- Isolated LLM module for commit review support.

**Speaker explanation**

- This is not a mockup.
- The backend, the UI, and the main analysis flow are already implemented and usable.

**Visual suggestion**

- Use a checklist, a product screenshot, or a simple capability grid.
- Keep the focus on delivered features, not implementation detail.

---

## Slide 13 - Feedback

**Title**

Improvements made after feedback

**Main idea**

The presentation was updated to be clearer, shorter, and more focused on value.

**Slide content**

- Slides are now shorter and easier to read.
- Diagrams match the current implementation better.
- The demo is centered on one clear scenario.
- Requirements, architecture, and results are better separated.
- The before/after value is shown more clearly.

**Speaker explanation**

- We used the first feedback to improve clarity, not just to add more content.
- The current version is more structured and easier to present orally.

**Visual suggestion**

- Use a short checklist or a simple before/after layout.
- Add a quoted remark only if one feedback point must be shown exactly.

---

## Slide 14 - Closing

**Title**

Conclusion and next steps

**Main idea**

The system makes dependency analysis faster, clearer, and more useful for release decisions.

**Slide content**

- Azure DevOps stays the source of truth.
- The system automates traceability from work items to releases.
- It reduces manual effort and lowers the risk of missing information.
- It supports faster and clearer release decisions.

**Speaker explanation**

- Our main contribution is the automation of end-to-end traceability.
- The next steps can extend the dashboard, enrich more artifacts, and connect more sources.

**Visual suggestion**

- Use one final summary diagram or a clean takeaway slide.
- Keep the ending simple and confident.

---

## Recommended backup slides

- Swagger endpoint list.
- Backend module breakdown.
- SSE and batch processing.
- Commit module and LLM module separation.
- DTO structure and normalization.

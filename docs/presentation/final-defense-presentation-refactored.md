# MES-X Final Defense Presentation (Refactored)

## Presentation Objective
This version is refactored for a clear academic defense narrative:
- Problem to solution progression
- Minimal cognitive load for jury
- Strong logic in Design and Implementation
- Two coherent implementation modules only

---

## Slide 1 — Title
MES-X Dependency Management  
Presented by: Alaeddine Mdalla  
Forvia Informatique Tunisia — MES X.0 Division  
Academic Supervisor: Wafa Boumaiza  
Professional Supervisor: Khemiri Karima

## Slide 2 — Agenda
1. General Context
2. Requirements Analysis
3. Proposed Solution
4. Architecture and Methodology
5. Design and Implementation
6. System Demonstration (Traceability + AI Decision)
7. Conclusion

## Slide 3 — General Context
- Industry 4.0 and smart manufacturing context
- Increasing software dependency complexity
- Need to trace links between work items, pull requests, commits, and tags
- Missing unified dependency visibility for release preparation

## Slide 4 — Host Organization
Forvia:
- Global automotive leader (Faurecia + HELLA)
- Focus on smart manufacturing and software-driven factories

Forvia Informatique Tunisia:
- Software engineering hub
- MES X.0 division
- Microservices-based industrial systems

## Slide 5 — Existing Product Context
- MES ecosystem supports production systems
- Azure DevOps is the primary tracking platform
- Dependencies are implicit and mostly reconstructed manually

## Slide 6 — Existing Solution (Current Logic)
- Developers manually select work items
- Teams trace related pull requests and commits in Azure DevOps
- Dependency graph is reconstructed manually
- Results are copied into spreadsheet tracking

## Slide 7 — Problems of Existing System
- Not scalable
- Error-prone manual linking
- High time consumption
- Fragmented dependency view
- No unified decision support

---

## Slide 8 — Requirements Analysis
Functional and non-functional requirements baseline for automation.

## Slide 9 — Functional Requirements
- Resolve pull requests linked to work items
- Link pull requests to user stories
- Fetch commits and tags
- Build dependency graph
- Generate decision output
- Provide read-only traceability

## Slide 10 — Non-Functional Requirements
- Performance and scalability
- Reliability and fault tolerance
- Security and read-only access
- Maintainability through modular architecture
- Efficient API usage (batching and caching)
- MES architecture compliance

---

## Slide 11 — Proposed Solution
Core idea: automate dependency reconstruction using:
- Work items
- Pull requests
- Commits
- Tags
- Optional LLM analysis

## Slide 12 — Solution Overview (Executive Diagram)
```plantuml
@startuml
title MES-X Dependency Management - Executive View
left to right direction
skinparam shadowing false
skinparam defaultFontSize 15

actor User

rectangle "MES-X Platform" {
  [Select Work Items]
  [Trace Dependencies]
  [AI Analysis]
  [View Results]
}

rectangle "Outputs" {
  [Dependency Graph]
  [Traceability View]
  [Decision Overview]
}

User --> [Select Work Items]
[Select Work Items] --> [Trace Dependencies]
[Trace Dependencies] --> [AI Analysis]
[AI Analysis] --> [View Results]
[View Results] --> [Dependency Graph]
[View Results] --> [Traceability View]
[View Results] --> [Decision Overview]
@enduml
```

---

## Slide 13 — Agile Methodology
- Scrum methodology
- Azure DevOps for sprint tracking
- Iterative development cycles
- Continuous integration of modules

## Slide 14 — Project Iterations
- Setup and infrastructure
- Work item module
- Pull request module
- Commit module
- Sprint module
- Final integration

## Slide 15 — Architecture and Technologies
Insert full system architecture image.

## Slide 16 — CI/CD Pipeline
Insert CI/CD workflow image.

---

## Slide 17 — Design and Implementation (Section Intro)
Design and Implementation is presented as two logical parts:
1. Batch Related WorkItems
2. Commit Tags Fetch and AI Decision Support

This keeps the technical story linear and strong.

---

## Slide 18 — Part 1: Traceability Core Module
Focus: from user story selection to consolidated dependency scope.

## Slide 19 — Use Case Diagram (Batch Related WorkItems)
```plantuml
@startuml
title Use Case - Batch Related WorkItems
left to right direction

actor Developer
actor "LLM Provider" as LLM

rectangle "MES-X Traceability Core" {
  usecase "Select User Story / Work Item Set" as UC1
  usecase "Launch Batch Related Analysis" as UC2
  usecase "Traverse Related Dependencies" as UC3
  usecase "Produce Consolidated Scope" as UC4
}

Developer --> UC1
Developer --> UC2
UC2 --> UC3
UC3 --> UC4
LLM --> UC4
@enduml
```

## Slide 20 — Sequence Diagram (Batch Related Execution)
```plantuml
@startuml
title Sequence - Batch Related WorkItems
autonumber
hide footbox

actor Developer
participant UI
participant WorkItemAPI
participant PRService
participant CommitService
participant AzureDevOps

Developer -> UI: Select sprint/user stories
UI -> WorkItemAPI: getRelatedWorkItemsBatch(ids)
WorkItemAPI -> AzureDevOps: fetch work item graph
AzureDevOps --> WorkItemAPI: work items + links
WorkItemAPI -> PRService: resolve linked pull requests
PRService -> AzureDevOps: fetch PR metadata
AzureDevOps --> PRService: pull requests
PRService -> CommitService: fetch commits for resolved PRs
CommitService -> AzureDevOps: fetch commit metadata
AzureDevOps --> CommitService: commits
CommitService --> UI: consolidated trace scope
UI --> Developer: batch related dependency view
@enduml
```

## Slide 21 — Class Diagram (Traceability Core)
```plantuml
@startuml
title Class Diagram - Traceability Core

class WorkItemDto {
  +id: number
  +state: string
}

class WorkItemLinkDto {
  +type: string
  +isPR: boolean
}

class PullRequestSummaryDto {
  +prId: number
  +repositoryName: string
}

class CommitInfo {
  +commitId: string
  +repoName: string
}

WorkItemDto --> WorkItemLinkDto
WorkItemLinkDto --> PullRequestSummaryDto
PullRequestSummaryDto --> CommitInfo
@enduml
```

---

## Slide 22 — Use Case Diagram (Commit Tags and AI Decision)
```plantuml
@startuml
title Use Case - Commit Tags and AI Decision
left to right direction

actor Developer
actor "LLM Provider" as LLM

rectangle "MES-X Decision Layer" {
  usecase "Collect Commits from Traceability Scope" as UC1
  usecase "Fetch Commit Tags in Batch" as UC2
  usecase "Analyze Commit Context" as UC3
  usecase "Generate Decision Overview" as UC4
}

Developer --> UC1
UC1 --> UC2
UC2 --> UC3
UC3 --> UC4
LLM --> UC3
@enduml
```

## Slide 23 — Sequence Diagram (Commit Tags and AI Decision)
```plantuml
@startuml
title Sequence - Commit Tags and AI Decision
autonumber
hide footbox

actor Developer
participant DecisionAPI
participant WorkItemService
participant CommitService
participant LLM

Developer -> DecisionAPI: Request dependency decision overview
DecisionAPI -> WorkItemService: fetch scoped work items and PRs
WorkItemService --> DecisionAPI: work items + PR context
DecisionAPI -> CommitService: fetch commits and tags in batch
CommitService --> DecisionAPI: commit tag context
DecisionAPI -> LLM: optional AI review on selected commits
LLM --> DecisionAPI: insights and risk notes
DecisionAPI -> DecisionAPI: aggregate states and repository groups
DecisionAPI --> Developer: final decision overview
@enduml
```

## Slide 24 — Class Diagram (Decision Model)
```plantuml
@startuml
title Class Diagram - Decision Model

class DecisionInputSetDto {
  +workItems: DecisionInputWorkItemDto[]
  +repositories: RepoReferenceWithNameDto[]
}

class DecisionInputWorkItemDto {
  +id: number
  +state: string
}

class CommitInputDto {
  +commitId: string
  +tagBefore: string[]
  +tagAfter: string[]
  +exactTags: string[]
}

class DecisionAggregateResultDto {
  +doneWorkItems: DecisionInputWorkItemDto[]
  +otherWorkItems: DecisionInputWorkItemDto[]
}

DecisionInputSetDto --> DecisionInputWorkItemDto
DecisionInputSetDto --> CommitInputDto
DecisionAggregateResultDto --> DecisionInputWorkItemDto
@enduml
```

---

## Slide 25 — System Demonstration
Demonstration scenario:
1. Select sprint and batch work items
2. Generate related dependency scope
3. Fetch commit tags and repository context
4. Open decision overview
5. Trigger optional AI commit review

## Slide 26 — Conclusion
- MES-X replaces manual dependency reconstruction with a reproducible pipeline
- Traceability becomes faster, clearer, and decision-oriented
- Two-part logic keeps implementation and operation understandable
- Platform is ready for progressive AI-assisted release analysis

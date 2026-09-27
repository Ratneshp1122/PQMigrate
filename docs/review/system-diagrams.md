# PQMigrate review diagrams

The diagrams distinguish implemented behavior from planned work. Mermaid source remains editable and can be rendered later if requested.

## Current domain model

```mermaid
classDiagram
    class Finding {
      +String primitiveName
      +String filePath
      +int lineNumber
      +String role
      +String operation
      +String confidence
      +String detectionType
    }
    class CryptoIR {
      +String id
      +CryptoRole role
      +CryptoOperation operation
      +ProtocolContext protocolContext
      +String contextEvidence
    }
    class MigrationPlan {
      +String targetAlgorithm
      +String targetStandard
      +boolean patchAvailable
      +boolean requiresManualIntervention
      +String interventionReason
    }
    class DecisionTrace {
      trace_id
      outcome
      source_ref
      steps
      unresolved_fields
    }
    class PriorityAssessment {
      cryptographic_urgency
      evidence_strength
      migration_effort
      data_exposure
      overall_review_priority
    }
    class AssuranceRecord {
      +boolean testsPassed
      +boolean verifiedByHuman
    }
    class ProjectReport {
      +String schemaVersion
      +String scanId
      +String scannerVersion
      +String rulesVersion
      +int filesScanned
      +int totalFindings
    }
    ProjectReport "1" --> "0..*" AssuranceRecord
    AssuranceRecord "1" --> "1" CryptoIR
    AssuranceRecord "1" --> "0..1" MigrationPlan
    MigrationPlan "1" --> "1" DecisionTrace
    MigrationPlan "1" --> "1" PriorityAssessment
```

## Current CLI sequence

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant CLI
    participant Scanner as Python AST scanner
    participant Resolver as Bounded role analyzer
    participant Planner as Migration planner
    participant Report as JSON report
    Dev->>CLI: scan owned fixture
    CLI->>Scanner: enumerate and parse source
    Scanner-->>Resolver: findings and source paths
    Resolver-->>Planner: role, context, evidence or UNKNOWN
    Planner-->>Report: advisory plan or abstention
    Report-->>Dev: versioned JSON and policy exit code
```

## Backend scan lifecycle

```mermaid
stateDiagram-v2
    [*] --> Scanning
    Scanning --> Complete: worker exits 0 or 1 and valid JSON exists
    Scanning --> Failed: timeout, exception, missing or invalid JSON
    Complete --> [*]
    Failed --> [*]
```

`FAILED` never means zero findings. Missing worker output now fails closed.

## DFD level 0

```mermaid
flowchart LR
    U[Developer] -->|Owned source or approved repository reference| P((PQMigrate))
    R[Source repository] -->|Untrusted source snapshot| P
    P -->|Findings, evidence, coverage and advisory plans| U
```

## DFD level 1

```mermaid
flowchart LR
    U[Developer] -->|Scan request| P1((1. Enumerate source))
    R[Source repository] -->|Source files| P1
    P1 -->|Accepted files| P2((2. Parse and discover))
    P2 -->|Inventory leads| P3((3. Infer bounded role))
    P3 -->|Role and evidence or UNKNOWN| P4((4. Plan or abstain))
    K[(Versioned YAML knowledge base)] -->|Role predicates and advisory rules| P4
    P4 -->|Versioned report| D[(Report store or JSON file)]
    D -->|Authorized report| U
```

## Target extension after the review

SARIF/CBOM export, a labelled benchmark, isolated patch verification, and interoperability tests remain later milestones. They do not appear as completed processes in the current diagrams.

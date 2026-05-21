# Agents.md

# AI QA Multi-Agent Architecture

## Project Overview

This project is an AI-driven QA automation platform that uses:
- Confluence requirements
- Graph RAG
- LangGraph orchestration
- Multi-agent collaboration

to generate:
- intelligent test scenarios
- dependency-aware validations
- Gherkin scenarios
- QA review feedback

The platform is designed to understand:
- business workflows
- module relationships
- validation rules
- prerequisite dependencies
- authorization constraints

before generating test artifacts.

---

# High-Level Architecture

User Query
    ↓
Graph RAG Retrieval Layer
    ↓
Requirement Understanding Agent
    ↓
Dependency Mapping Agent
    ↓
Scenario Generation Agent
    ↓
Gherkin Generation Agent
    ↓
Review/Critic Agent
    ↓
Final Output

---

# Shared Intelligence Layer

## Graph RAG Knowledge Layer

All agents use the shared Graph RAG retrieval system.

The Graph RAG layer provides:
- semantic retrieval
- graph relationship retrieval
- workflow dependency discovery
- business rule retrieval
- validation rule retrieval

---

# Graph Data Sources

## Confluence Pages
- Project Overview
- Business Workflows
- Trade Management
- Authentication & Authorization
- Settlement
- Validation Rules
- Use Case Pages

---

# Graph Relationships

The graph contains relationships such as:

- DEPENDS_ON
- REQUIRES
- BLOCKS
- VALIDATES
- ALLOWS
- RELATED_TO

Example:

Trade Amendment
    DEPENDS_ON → Trade Approval

Settlement
    BLOCKS → Trade Amendment

Supervisor
    ALLOWS → Trade Approval

---

# Shared Agent State

The orchestration state shared across agents includes:

```python
{
    "user_query": "",
    "retrieved_context": [],
    "structured_requirements": {},
    "dependencies": [],
    "generated_scenarios": [],
    "gherkin_scenarios": [],
    "review_feedback": [],
    "final_output": ""
}
```

---

# 1. Requirement Understanding Agent

## Purpose

Transforms retrieved requirement context into structured business understanding.

This agent extracts:
- actors
- preconditions
- business rules
- validations
- workflow states
- APIs
- error conditions

---

## Responsibilities

- Analyze retrieved Confluence requirements
- Extract structured business logic
- Normalize requirement data
- Identify workflow constraints
- Prepare context for downstream agents

---

## Inputs

- User query
- Retrieved Graph RAG context

Example:

```text
Generate testcases for Trade Amendment
```

---

## Outputs

```python
{
    "module": "Trade Management",
    "use_case": "Trade Amendment",
    "actors": ["Trader"],
    "preconditions": [
        "Trade approved",
        "Trade not settled"
    ],
    "business_rules": [
        "Settled trades cannot be amended"
    ],
    "validations": [
        "Quantity > 0"
    ]
}
```

---

## Uses Graph RAG For

- Requirement retrieval
- Business rule extraction
- Validation extraction
- Workflow understanding

---

## Failure Conditions

- Missing requirements
- Incomplete business rules
- Ambiguous workflows

---

# 2. Dependency Mapping Agent

## Purpose

Identifies related workflows, prerequisite use cases,
authorization dependencies, and blocked transitions.

This agent provides dependency-aware intelligence.

---

## Responsibilities

- Analyze graph relationships
- Discover prerequisite workflows
- Identify blockers and dependencies
- Retrieve related validation rules
- Build dependency context

---

## Inputs

- Structured requirement output
- Graph RAG relationships

---

## Outputs

```python
{
    "dependencies": [
        "Trade Approval",
        "Authentication"
    ],
    "blocked_by": [
        "Settlement"
    ],
    "related_modules": [
        "Authorization",
        "Validation Rules"
    ]
}
```

---

## Uses Graph RAG For

- Graph traversal
- Dependency discovery
- Relationship analysis
- Cross-module retrieval

---

## Important Relationships

- DEPENDS_ON
- BLOCKS
- REQUIRES
- VALIDATES

---

## Failure Conditions

- Missing dependency mapping
- Cyclic dependencies
- Incomplete graph relationships

---

# 3. Scenario Generation Agent

## Purpose

Generates intelligent QA test scenarios using:
- business rules
- validations
- dependencies
- workflow states

---

## Responsibilities

Generate:
- positive scenarios
- negative scenarios
- edge cases
- authorization tests
- workflow transition tests
- validation tests

---

## Inputs

- Structured requirements
- Dependency context
- Validation rules

---

## Outputs

```python
[
    "Verify amendment of approved trade",
    "Verify settled trades cannot be amended",
    "Verify unauthorized user cannot amend trade",
    "Verify amendment rejected for invalid quantity"
]
```

---

## Scenario Categories

### Positive Scenarios
Expected successful behavior.

### Negative Scenarios
Invalid operations and validations.

### Edge Cases
Boundary and unusual conditions.

### Dependency-Aware Scenarios
Cross-workflow validation scenarios.

---

## Uses Graph RAG For

- Similar scenario retrieval
- Validation rule retrieval
- Workflow relationship retrieval

---

## Failure Conditions

- Duplicate scenarios
- Missing coverage
- Weak validations

---

# 4. Gherkin Generation Agent

## Purpose

Converts generated scenarios into BDD Gherkin format.

---

## Responsibilities

Generate:
- Given
- When
- Then
- And

statements from plain scenarios.

---

## Inputs

- Generated test scenarios

---

## Outputs

```gherkin
Scenario: Amend approved trade

Given an approved trade exists
When the user modifies quantity
Then the trade should be amended successfully
```

---

## Supported Features

- Scenario outlines
- Parameterized examples
- Preconditions
- Negative validations

---

## Uses Graph RAG For

Optional:
- Workflow wording consistency
- Business terminology alignment

---

## Failure Conditions

- Invalid Gherkin syntax
- Missing Given/Then steps
- Ambiguous scenarios

---

# 5. Review/Critic Agent

## Purpose

Acts as a senior QA reviewer to improve quality,
coverage, and completeness.

---

## Responsibilities

Review:
- missing scenarios
- duplicate scenarios
- weak validations
- incomplete dependency coverage
- missing negative cases
- authorization gaps

---

## Inputs

- Generated scenarios
- Gherkin output
- Original requirement context

---

## Outputs

```python
{
    "missing_scenarios": [
        "Invalid Trade ID validation"
    ],
    "duplicates": [],
    "improvements": [
        "Add authorization validation scenarios"
    ]
}
```

---

## Review Categories

### Requirement Coverage
Checks all business rules covered.

### Validation Coverage
Checks validation scenarios present.

### Dependency Coverage
Checks prerequisite workflows validated.

### Authorization Coverage
Checks role-based validations.

### Edge Case Coverage
Checks abnormal scenarios.

---

## Uses Graph RAG For

- Cross-checking requirements
- Validation verification
- Dependency verification

---

## Failure Conditions

- Low coverage
- Duplicate scenarios
- Missing dependency validation

---

# LangGraph Orchestration Layer

## Purpose

Coordinates:
- state management
- agent sequencing
- retries
- conditional routing
- review loops

---

# Workflow Sequence

Requirement Understanding Agent
        ↓
Dependency Mapping Agent
        ↓
Scenario Generation Agent
        ↓
Gherkin Generation Agent
        ↓
Review/Critic Agent

---

# Retry Flow

If Review Agent detects missing coverage:

Review Agent
    ↓
Scenario Generation Agent
    ↓
Regenerate scenarios
    ↓
Review Again

---

# Shared Retrieval Interface

All agents use the same retrieval abstraction.

Example:

```python
retrieve_context(query)
```

The retrieval layer internally combines:
- semantic search
- graph traversal
- dependency retrieval

---

# Future Enhancements

## Planned Future Agents

### Coverage Analysis Agent
Calculates testcase coverage percentage.

### Automation Script Generation Agent
Generates Playwright/Cucumber scripts.

### Historical Defect Learning Agent
Learns from Jira defects.

### Risk-Based Testing Agent
Prioritizes high-risk scenarios.

### API Test Generation Agent
Generates API testcases from APIs.

---

# Design Principles

- Shared Graph RAG intelligence layer
- Stateless agents where possible
- Specialized agent responsibilities
- Dependency-aware reasoning
- Workflow-aware testcase generation
- Validation-driven QA generation

---

# Key Architectural Insight

Graph RAG provides:
- knowledge retrieval
- dependency relationships
- contextual intelligence

Agents provide:
- specialized reasoning
- transformation
- QA generation
- quality validation

The intelligence of the platform comes from:
- contextual retrieval
- workflow relationships
- dependency understanding

not from LLM prompting alone.
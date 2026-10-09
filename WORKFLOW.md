# Team GitHub Workflow & Development Conventions

This document defines the engineering workflow, git branching rules, commit message standards, code review process, and issue tracking methodology for the **LeaveHRAlone** (PolicyPilot AI) project team.

---

## 1. Branching Strategy

Our team enforces a disciplined, feature-branch-based workflow to keep the main codebase stable and deployable at all times.

- **Main Branch (`main`)**:
  - Contains strictly production-ready, releasable code.
  - Direct commits to `main` are prohibited. All changes must arrive via approved Pull Requests.
- **Feature & Task Branches**:
  - All new work must be developed on dedicated short-lived branches created from `main`.
  - Naming Convention: `[type]/[short-description]`
    - `feature/`: New capabilities or user-facing enhancements (e.g., `feature/data-ingestion-pipeline`)
    - `fix/`: Bug fixes or logic corrections (e.g., `fix/validation-logic`)
    - `docs/`: Documentation updates or additions (e.g., `docs/workflow-and-readme`)
    - `refactor/`: Code restructuring without functional changes (e.g., `refactor/vector-retriever`)
    - `chore/`: Dependency updates, build configurations, or maintenance (e.g., `chore/update-requirements`)
- **Branch Lifecycle & Cleanup**:
  - Feature branches are kept up to date with `main`.
  - Once a Pull Request is approved and merged into `main`, the remote and local feature branches are deleted immediately.

---

## 2. Commit Message Conventions

We follow the Conventional Commits standard (`[type]: [description]`).

### Format
```text
[type]: [short summary in present tense]

[optional body explaining why the change was made, context, and key decisions]
```

### Commit Types
| Type | Usage | Example |
| --- | --- | --- |
| `feat` | New feature or capability | `feat: add data validation function for incoming CSVs` |
| `fix` | Bug fix or issue resolution | `fix: resolve region metadata filtering leak in retriever` |
| `docs` | Documentation changes | `docs: document team github workflow and conventions` |
| `refactor` | Code restructuring | `refactor: extract chunk processing logic into pipeline module` |
| `test` | Adding or updating unit/integration tests | `test: add unit tests for document chunking parser` |
| `chore` | Dependency/config maintenance | `chore: update requirements.txt with qdrant-client` |

### Why We Use This Convention
- **Automated Changelog Generation**: Clean commit history enables automated releases and release notes.
- **Readability & Auditability**: Team members can easily scan history and understand the purpose of each change without reading full diffs.
- **Improved Code Reviews**: Reviewers can evaluate changes step-by-step per atomic commit.

---

## 3. Pull Request (PR) & Review Process

All code additions and documentation updates must be reviewed prior to merging.

### PR Requirements
- **Descriptive Title**: State clearly what the PR accomplishes (e.g., `Add data validation workflow and team branching guidelines`).
- **Context & Summary**: Explain what changed, why the change was made, and how it was implemented.
- **Linked Issues**: Every PR must reference at least one GitHub issue using closing keywords (`Closes #1`, `Fixes #2`).
- **Commit History Summary**: Provide a brief outline or bulleted list of the commits included.
- **Testing Verification**: Document test steps performed and evidence of verification.

### Review Criteria
- **Approvals**: Every PR requires at least **one approval** from a team reviewer before merging.
- **Focus Areas**:
  1. **Correctness**: Logic behaves as specified in the PRD without unhandled edge cases.
  2. **Data Integrity & Security**: Ensures metadata filtering (e.g., region isolation) prevents data leakage.
  3. **Clarity & Code Quality**: Code is readable, properly modularized, and maintainable.
  4. **Test Coverage**: Appropriate unit/integration tests are included for new functionality.
  5. **Commit Message Compliance**: Commit messages adhere to the conventional format.
- **Open PR State**: PRs remain open until all review feedback is resolved and approvals are granted.

---

## 4. GitHub Issue Tracking Approach

We use GitHub Issues as the single source of truth for sprint planning and task management.

- **Issue-First Development**: Every feature, bug fix, analytical task, or documentation improvement starts with a dedicated GitHub Issue before branch creation.
- **Issue Structure**:
  - **Action-Oriented Title**: Clear, specific title stating the task (e.g., `Ingest HR policy documents into vector database pipeline`).
  - **Detailed Description**: Contains a "Why This Work Matters" context section and explicit "What Done Means" criteria.
  - **Labels**: Every issue is assigned appropriate metadata labels (e.g., `feature`, `documentation`, `data-pipeline`).
  - **Assignee**: Assigned to the developer responsible for delivering the work.
- **Automatic Closure**: Issues are automatically closed when their corresponding PR is merged into `main` using `Closes #<issue-number>` syntax.

---

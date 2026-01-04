# Task Management Workflow

## Overview

Comprehensive task tracking and project state management for agentic development workflows. This document codifies learnings from production projects using multi-agent AI development patterns.

**Purpose**: Establish a single source of truth for project state that enables seamless context handoff between sessions, agents, and developers.

---

## Core Principles

### 1. Single Source of Truth

The `tasks.md` file is the canonical reference for:
- Current project phase and active tasks
- Completed work with timestamps and artifacts
- Key decisions and their rationale
- Session logs for context continuity
- Notes for future agents

### 2. XP Programming Integration

Task management integrates with Extreme Programming practices:

| XP Practice | Task Integration |
|-------------|------------------|
| **TDD** | Tasks specify test requirements before implementation |
| **Small Steps** | Tasks decomposed into commit-sized units |
| **Continuous Integration** | Tasks include quality gate verification |
| **Collective Ownership** | Tasks assigned to phases, not individuals |

### 3. Agentic Workflow Phases

**Phase 1: Design (Architect Agent)**
- Create design document in `docs/design/`
- Define interfaces and data structures
- Document architectural decisions in ADRs
- Output: Design doc with clear specifications

**Phase 2: Implementation (Developer Agent)**
- Follow TDD cycle: Red → Green → Refactor
- Write tests before implementation
- Commit frequently with descriptive messages
- Output: Working code with test coverage

**Phase 3: Validation (QA Agent)**
- Verify test coverage meets targets (≥70%)
- Run full test suite and linting
- Check code quality and patterns
- Output: Quality report and approval

---

## Task File Structure

### Recommended `tasks.md` Format

```markdown
# [Project Name] - Task Tracking

> **Source of Truth**: This file is the single source of truth for project state.

## Table of Contents
- [How to Use This File](#how-to-use-this-file)
- [XP Programming Flow](#xp-programming-flow)
- [Project Timeline](#project-timeline)
- [Current Work](#current-work)
- [Completed Phases](#completed-phases)
- [Task History Archive](#task-history-archive)
- [Notes for Future Agents](#notes-for-future-agents)

---

## Current Work

### Active Tasks

| Task | Status | Notes |
|------|--------|-------|
| Description | ✅/🔄/⏳ | Optional context |

### Up Next - Priority Tasks

#### 🔴 Critical (Immediate)
| Task | Status | Priority | Notes |
|------|--------|----------|-------|

#### 🟠 High Priority (Next Sprint)
| Task | Status | Priority | Notes |
|------|--------|----------|-------|

#### 🟡 Medium Priority (This Quarter)
| Task | Status | Priority | Notes |
|------|--------|----------|-------|

---

## Notes for Future Agents

### Project State
- **Current Phase**: [Phase description]
- **Test Coverage**: [X% (N tests)]
- **CI/CD**: [Status]
- **Pre-commit**: [Hooks installed]

### Key Files to Review
- [List critical files with descriptions]

### Agent Integration Status
| Agent | In Flow | Standalone | Notes |
|-------|---------|------------|-------|
```

---

## Status Icons

| Icon | Meaning | When to Use |
|------|---------|-------------|
| ✅ | Complete | Task finished and verified |
| 🔄 | In Progress | Currently being worked on |
| ⏳ | Blocked/Pending | Waiting on dependency or decision |
| ❌ | Failed/Cancelled | Task abandoned or failed |

---

## Session Logging

### Session Log Format

```markdown
### Session Log: YYYY-MM-DD

**Session Focus**: [Brief description of work focus]

**Key Decisions**:
1. Decision 1 with rationale
2. Decision 2 with rationale

**Branch**: `[branch-name]`
**Commit**: `[commit-hash]`

**Artifacts Created**:
- `path/to/file.py` - Description (N lines)

**Files Modified**:
- `path/to/file.py` - What changed

**Quality Gates Passed**:
- N tests passing (was M)
- X% test coverage
- All linting/type checks passing

**Next Steps**:
- [ ] Task 1
- [ ] Task 2
```

### Session Lifecycle

1. **Session Start**
   ```bash
   # 1. Check current state
   cat tasks.md
   git status && git branch

   # 2. Verify environment
   make test  # or uv run pytest

   # 3. Create feature branch
   git checkout -b feature/descriptive-name
   ```

2. **During Session**
   - Update task status to 🔄 when starting
   - Commit every 15-30 minutes
   - Update tasks.md every 30 minutes
   - Run quality gates before each commit

3. **Session End**
   ```bash
   # 1. Full validation
   make test && make lint

   # 2. Update tasks.md with session log
   # Mark completed items with ✅

   # 3. Final commit
   git add .
   git commit -m "feat: complete feature X"

   # 4. Push
   git push origin feature/name
   ```

---

## Task Decomposition Patterns

### Feature Tasks

Break large features into implementation-sized tasks:

```markdown
### Feature: User Authentication

| Task | Status | Notes |
|------|--------|-------|
| Create design document | ✅ | `docs/design/auth.md` |
| Define Pydantic models | ✅ | User, Token models |
| Implement password hashing | ✅ | bcrypt, 10 rounds |
| Add login endpoint | ✅ | POST /auth/login |
| Add tests for login | ✅ | 15 tests, 95% coverage |
| Add registration endpoint | 🔄 | POST /auth/register |
| Add tests for registration | | |
| Add password reset flow | | |
| Update documentation | | |
```

### Bug Fix Tasks

```markdown
### Bug: Session expires too quickly

| Task | Status | Notes |
|------|--------|-------|
| Reproduce issue | ✅ | Sessions expire after 5 min |
| Root cause analysis | ✅ | TTL misconfigured in Redis |
| Write failing test | ✅ | `test_session_ttl_24_hours` |
| Implement fix | ✅ | Updated REDIS_SESSION_TTL |
| Verify fix | ✅ | Test passes, manual verification |
| Update documentation | ✅ | Added env var to README |
```

### Refactoring Tasks

```markdown
### Refactor: Split large module

| Task | Status | Notes |
|------|--------|-------|
| Identify extraction targets | ✅ | 3 logical modules identified |
| Create new module structure | ✅ | routes/, handlers/, models/ |
| Move route handlers | ✅ | 5 files created |
| Move business logic | ✅ | 3 handler files |
| Move Pydantic models | ✅ | requests.py, responses.py |
| Update imports | ✅ | All tests passing |
| Run quality gates | ✅ | 444 tests, 72% coverage |
| Remove old code | ✅ | main.py 2133→5 lines |
```

---

## Priority Matrix

### Priority Levels

| Level | Label | Response Time | Examples |
|-------|-------|---------------|----------|
| 🔴 | Critical | Immediate | Security vulnerabilities, production bugs, blocking issues |
| 🟠 | High | Next sprint | Major features, technical debt, performance issues |
| 🟡 | Medium | This quarter | Enhancements, nice-to-haves, refactoring |
| 🟢 | Low | Backlog | Documentation, minor improvements |

### Priority Assignment Criteria

**Critical (🔴)**:
- Blocks other work
- Affects production stability
- Security implications
- Data integrity issues

**High (🟠)**:
- Required for next release
- Technical debt causing friction
- Performance degradation >20%
- Missing critical tests

**Medium (🟡)**:
- Improves developer experience
- Code quality improvements
- Test coverage gaps
- Documentation updates

**Low (🟢)**:
- Nice-to-have features
- Minor optimizations
- Style improvements
- Edge case handling

---

## Quality Gates Integration

### Pre-Task Checklist

Before starting any task:
- [ ] Read current tasks.md state
- [ ] Check git status and branch
- [ ] Verify tests pass
- [ ] Understand dependencies

### Post-Task Checklist

Before marking a task complete:
- [ ] All tests pass
- [ ] Coverage maintained or improved
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] tasks.md updated

### Quality Metrics to Track

```markdown
### Quality Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | ≥70% | 75% |
| Python Tests | Pass | 444/444 |
| JS Tests | Pass | 415/415 |
| Lint Errors | 0 | 0 |
| Type Errors | 0 | 0 |
```

---

## Agent Handoff Protocol

### Context Handoff

When switching between agents or sessions:

1. **Document Current State**
   - Update tasks.md with all progress
   - Note any blockers or decisions needed
   - List files modified

2. **Commit All Changes**
   - Include meaningful commit messages
   - Reference task IDs if applicable

3. **Create Session Log**
   - Summarize what was done
   - Document key decisions
   - List artifacts created

4. **Update Notes for Future Agents**
   - Project state summary
   - Key files to review
   - Known issues or warnings

### Context Recovery

When starting a new session:

1. **Read tasks.md** first
2. **Check git status** and recent commits
3. **Review session logs** for context
4. **Verify environment** works (tests pass)
5. **Create feature branch** if needed

---

## Examples from Production

### Example: Backend Improvements Session

```markdown
### Session Log: 2026-01-03

**Session Focus**: Backend Improvements - Modular API, Rate Limiting, CORS

**Key Decisions**:
1. Split 2133-line main.py into modular structure using FastAPI app factory pattern
2. Implemented privacy-first rate limiting using session_id only (NO IP tracking)
3. Made CORS configurable via settings (permissive dev, restrictive prod)
4. Used APIRouter for modular route organization

**Branch**: `backend-improvements`
**Commit**: `778ebb0`

**Artifacts Created**:
- `src/api/app.py` - App factory with lifespan and middleware (143 lines)
- `src/api/rate_limiting.py` - Privacy-first rate limiter (153 lines)
- `src/api/dependencies.py` - Shared dependencies (87 lines)
- `src/api/routes/` - Route modules (adventure, combat, agents, health)
- `src/api/handlers/` - Business logic handlers (character, quest, combat)
- `tests/test_rate_limiting.py` - 35 rate limiting tests

**Quality Gates Passed**:
- 444 Python tests passing (was 409)
- 35 new rate limiting tests
- 8 E2E Playwright tests passing
- All linting/type checks passing
```

---

## Quick Reference

### Task Table Template

```markdown
| Task | Status | Notes |
|------|--------|-------|
| Task description | ✅/🔄/⏳ | Optional context |
```

### Commit Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no behavior change) |
| `test` | Adding tests |
| `docs` | Documentation |
| `chore` | Maintenance |

### Quick Commands

```bash
# Start session
cat tasks.md && git status && git branch

# During work
make test && git add . && git commit

# End session
make test && make lint && git push
```

---

## Related Documents

- **[feature-development.md](feature-development.md)** - Feature implementation workflow
- **[bug-fix.md](bug-fix.md)** - Bug fix process
- **[multi-agent-coordination.md](multi-agent-coordination.md)** - Agent handoff patterns
- **[../quality-gates/](../quality-gates/)** - Quality gate configurations

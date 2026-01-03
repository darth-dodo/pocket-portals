# Feature: Backend Improvements

## Overview

Refactor the monolithic `src/api/main.py` (2133 lines) into modular structure, add rate limiting, and fix production CORS configuration.

**Business Value**: Improved maintainability, API abuse protection, production-ready security.

## Requirements

### Functional
- Rate limiting: 20/min LLM endpoints, 60/min combat, 100/min default
- CORS: Allow all origins in dev, configurable allow-list in production
- Modular code: main.py split into routes/, handlers/, models/

### Non-functional
- Privacy-first: Rate limiting uses session_id only (no IP tracking)
- All 409 existing tests must pass
- No breaking changes to API contracts

## Architecture

### Target Structure

```
src/api/
├── __init__.py
├── app.py                # App factory, lifespan, middleware
├── main.py               # Simplified entry point
├── rate_limiting.py      # Rate limit middleware (DONE)
├── content_safety.py     # BLOCKED_PATTERNS, filter_content
├── constants.py          # Narrative text, choices
├── dependencies.py       # get_session, build_context
├── models/
│   ├── __init__.py
│   ├── requests.py       # ActionRequest, ResolveRequest, etc.
│   └── responses.py      # NarrativeResponse, etc.
├── routes/
│   ├── __init__.py
│   ├── adventure.py      # /start, /action, /action/stream
│   ├── combat.py         # /combat/*
│   ├── agents.py         # /innkeeper, /keeper, /jester
│   └── health.py         # /health
└── handlers/
    ├── __init__.py
    ├── character.py      # Character creation handlers
    ├── quest.py          # Quest selection handlers
    └── combat.py         # Combat action handlers
```

### Rate Limiting Design

```python
# Privacy-first: session_id only, no IP tracking
class RateLimiter:
    def _get_session_id(request: Request) -> str:
        # 1. Check X-Session-ID header
        # 2. Check query params
        # 3. Fallback to "anonymous" bucket

    def check_rate_limit(request, limit, window=60):
        # Raises HTTPException(429) if exceeded
```

**Rate Limit Tiers**:
| Endpoint Type | Limit | Endpoints |
|---------------|-------|-----------|
| LLM-heavy | 20/min | /action, /action/stream, /keeper/resolve, /jester/complicate |
| Combat | 60/min | /combat/start, /combat/action |
| Default | 100/min | /start, /health |

### CORS Design

```python
# Development: permissive
allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]

# Production: configured via settings
allow_origins=settings.cors_origins  # ["http://localhost:8000", ...]
allow_methods=settings.cors_allow_methods  # ["GET", "POST", "OPTIONS"]
allow_headers=settings.cors_allow_headers  # ["Content-Type", "X-Session-ID"]
```

## Dependencies

- `ratelimit>=2.2.1` - Rate limiting library (added to pyproject.toml)
- No new external dependencies for CORS or module split

## Implementation Plan

### Phase 1: Rate Limiting (DONE)
1. ✅ Add ratelimit dependency
2. ✅ Add settings to src/config/settings.py
3. ✅ Create src/api/rate_limiting.py
4. ⏳ Add tests for rate_limiting.py
5. ⏳ Apply rate limits to endpoints

### Phase 2: CORS Fix
1. ✅ Add CORS settings to src/config/settings.py
2. ⏳ Update middleware in main.py
3. ⏳ Add CORS tests

### Phase 3: Module Split (Incremental)
1. Extract constants.py (lines 207-238)
2. Extract content_safety.py (lines 55-190)
3. Extract models/ (lines 320-430)
4. Extract dependencies.py (lines 241-318)
5. Extract handlers/ (lines 863-1491)
6. Extract routes/ (lines 501-861, 1494-2114)
7. Create app.py with app factory
8. Simplify main.py to entry point

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Circular imports during split | Extract leaf modules first (constants, models) |
| Breaking existing tests | Run `make test` after each extraction step |
| Agent access in routes | Move agents to app.state, access via request.app.state |

## Testing Strategy

- **Unit Tests**: 35 tests for rate_limiting.py (100% coverage)
- **Integration**: Verify endpoints return 429 when rate limited
- **Regression**: All 409 existing tests must pass after each step
- **E2E**: Manual verification of gameplay flow

## Session Log

### Session 1: Initial Setup (2026-01-03)
**Agent**: Architect → Developer
**Duration**: In progress

**Completed**:
- [x] Created branch `backend-improvements`
- [x] Updated tasks.md with 🔄 status
- [x] Added ratelimit dependency to pyproject.toml
- [x] Added rate limit + CORS settings to settings.py
- [x] Created src/api/rate_limiting.py

**In Progress**:
- [ ] Rate limiting tests
- [ ] CORS middleware update
- [ ] Module extraction

**Next Steps**:
- Complete rate limiting tests
- Update CORS middleware
- Begin module extraction (constants.py first)

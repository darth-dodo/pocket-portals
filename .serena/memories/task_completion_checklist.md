# Task Completion Checklist

## Before Committing

### 1. Run Tests
```bash
make test
```
- All tests must pass
- Coverage should be ≥70% (target 80%+)

### 2. Run Linting
```bash
make lint
```
- No ruff errors
- Code properly formatted

### 3. Full Quality Gate (optional but recommended)
```bash
make check  # Runs both lint and test
```

## TDD Workflow

### Red → Green → Refactor Cycle
1. **RED**: Write failing test first
   ```bash
   make test-fast  # Should fail
   ```

2. **GREEN**: Write minimal code to pass
   ```bash
   make test-fast  # Should pass
   ```

3. **REFACTOR**: Clean up code
   ```bash
   make test       # Should still pass
   ```

4. **COMMIT**: Quality gates then commit
   ```bash
   make check
   git add . && git commit -m "feat: description"
   ```

## Git Commit Message Format

```
<type>: <description>

<optional body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Update tasks.md

After completing work, update `tasks.md`:
1. Mark completed tasks with ✅
2. Add notes about what was done
3. Document any blockers or decisions

## Session End Checklist

- [ ] All tests passing (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] `tasks.md` updated with progress
- [ ] Feature branch committed
- [ ] No temporary files left behind (`make clean`)

## Quality Targets

| Metric | Target |
|--------|--------|
| Test Coverage | ≥70% (aim for 80%+) |
| All Tests Pass | 100% |
| Lint Errors | 0 |
| Commit Frequency | Every working increment |

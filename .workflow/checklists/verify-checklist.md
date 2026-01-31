# Verification Checklist

Complete this checklist during the VERIFY phase before proceeding to SHIP.

---

## Pre-Verification Gate

- [ ] EXECUTE phase completed
- [ ] All planned tasks marked done in plan.md
- [ ] Session documentation up to date

---

## 1. Automated Tests

### Unit Tests
- [ ] All existing tests passing
- [ ] New tests written for new functionality
- [ ] Edge cases covered
- [ ] Error conditions tested

### Integration Tests
- [ ] Component interactions tested
- [ ] API endpoints tested (if applicable)
- [ ] Database operations tested

### Test Commands (this project)
```bash
npm test                    # Run all tests (pytest)
pytest tests/ -v            # Direct pytest
pytest tests/ -v --cov      # With coverage (if pytest-cov installed)
```

### Test Results
- **Total Tests:** ___
- **Passing:** ___
- **Failing:** ___
- **Coverage:** ___%

---

## 2. AI Code Review (Gemini)

### Running AI Review
```bash
# Full review (included in verify.js)
npm run workflow:verify

# Standalone AI review
npm run workflow:ai-review

# Review git diff only
npm run workflow:ai-review:diff

# Security-focused review
npm run workflow:ai-review:security
```

### Security Review Results
- [ ] AI security review completed
- Security Risk Level: LOW / MEDIUM / HIGH / CRITICAL
- Security Issues Found: ___

| Severity | Location | Issue | Resolution |
|----------|----------|-------|------------|
|          |          |       |            |

### Quality Review Results
- [ ] AI quality review completed
- Code Quality: EXCELLENT / GOOD / ACCEPABLE / NEEDS_WORK
- Quality Issues Found: ___

| Priority | Location | Issue | Resolution |
|----------|----------|-------|------------|
|          |          |       |            |

### AI Review Sign-off
- [ ] All CRITICAL issues addressed
- [ ] All HIGH severity security issues addressed
- [ ] Quality issues reviewed and addressed or documented
- [ ] Accepted risks documented in session notes

**AI Review Result:** `.workflow/state/ai-review.json`

---

## 3. Visual Verification

### Manual UI Testing (if applicable)
- [ ] Feature works as expected
- [ ] Error states display correctly
- [ ] Loading states display correctly

### Screenshot Evidence
Capture screenshots for UI changes if applicable.

**Evidence Location:** `.workflow/evidence/SESSION-ID/`

---

## 4. Code Quality

### Linting (this project)
- [ ] Ruff passes with no errors
- [ ] No new warnings introduced

```bash
npm run lint
# or: ruff check . && ruff format --check .
```

### Formatting
- [ ] Ruff format applied
- [ ] Consistent code style

```bash
ruff format .
```

---

## 5. Security Review (Manual)

- [ ] Security checklist completed (see security-review.md)
- [ ] `npm run audit` (pip-audit) shows no high/critical issues
- [ ] No secrets in committed code
- [ ] Input validation in place
- [ ] AI security findings addressed

```bash
npm run audit
```

---

## 6. File Integrity

### Generate Verification State
Run the verify script to generate file hashes:

```bash
npm run workflow:verify
```

This creates `.workflow/state/verify-state.json` containing:
- SHA256 hashes of source and test files
- Timestamp of verification
- Test results summary
- AI review summary
- Verification checklist status

### Verify Output
- [ ] `verify-state.json` generated successfully
- [ ] `ai-review.json` generated (if GEMINI_API_KEY set)
- [ ] All file hashes recorded
- [ ] No unexpected files modified

---

## 7. Documentation

- [ ] Code comments added where needed
- [ ] README updated (if public API changed)
- [ ] Session documentation complete
- [ ] Plan.md verification section updated
- [ ] AI review findings documented

---

## Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| Automated Tests | Pass/Fail | |
| AI Security Review | Pass/Needs Attention | Risk: |
| AI Quality Review | Pass/Needs Attention | Quality: |
| Visual Verification | Pass/Fail | |
| Code Quality | Pass/Fail | |
| Security Review | Pass/Fail | |
| File Integrity | Pass/Fail | |
| Documentation | Pass/Fail | |

---

## Human Checkpoint

**STOP:** Do not proceed to SHIP until this verification is complete.

- [ ] All checks above are passing
- [ ] AI review findings addressed or documented
- [ ] Any failures have been addressed or documented
- [ ] Human has reviewed verification results

**Verified by:** _______________  
**Date:** _______________  
**Decision:** APPROVED FOR SHIP / NEEDS WORK / APPROVED WITH CAVEATS

**Notes:**

---

## Proceeding to Ship

If verification passes:
1. Ensure `verify-state.json` is committed (optional, for PR evidence)
2. Run `npm run workflow:ship` to validate integrity and optionally create PR
3. Complete PR template with verification evidence
4. Include AI review summary in PR description

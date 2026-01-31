## Summary

<!-- 1-3 bullet points describing what this PR does -->
- 
- 

## Plan Reference

**Plan:** [SESSION-ID plan.md](link)  
**Session(s):** [SESSION-ID session.md](link)

## Changes

### Added
- 

### Changed
- 

### Removed
- 

## Security Checklist

<!-- From .workflow/checklists/security-review.md -->

- [ ] Input validation applied to all user inputs
- [ ] No sensitive data in logs or error messages
- [ ] SQL queries use parameterized statements (if applicable)
- [ ] File paths validated against traversal attacks
- [ ] Dependencies checked for vulnerabilities (`npm run audit` / pip-audit)
- [ ] No secrets or credentials in code

## Verification Evidence

### Automated Tests
- [ ] All tests passing
- [ ] Test coverage: X%
- New tests:
  - `tests/test_*.py` - [description]

### Visual Verification
- [ ] UI manually tested (if applicable)
- Screenshots: 
  - ![Screenshot description](.workflow/evidence/SESSION-ID/screenshot.png)

### File Integrity
- [ ] `verify-state.json` generated
- [ ] File hashes match verified state

## Deployment Notes

<!-- Any special deployment considerations -->

- [ ] No database migrations required
- [ ] No environment variable changes
- [ ] No breaking API changes

## Reviewer Notes

<!-- Anything reviewers should pay special attention to -->

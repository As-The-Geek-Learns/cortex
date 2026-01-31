# Security Review Checklist

Use this checklist during the VERIFY phase and before shipping any code changes.

---

## Input Validation & Sanitization

- [ ] All user inputs are validated before use
- [ ] Text inputs are sanitized (HTML tags, control characters removed)
- [ ] Numeric inputs have bounds checking
- [ ] File paths are validated (no path traversal `../`)
- [ ] URLs are validated if accepting external links
- [ ] JSON/data imports are validated before processing

### Validation Patterns (Python)

```python
# GOOD - Centralized validation
from pathlib import Path
def safe_path(user_path: str) -> Path:
    resolved = Path(user_path).resolve()
    if not str(resolved).startswith(str(base_dir)):
        raise ValueError("Path traversal not allowed")
    return resolved

# BAD - No validation
path = user_input  # Raw input used directly
```

---

## Database Operations

- [ ] All queries use parameterized statements (no string concatenation)
- [ ] User inputs are never interpolated into SQL
- [ ] Database errors are caught and sanitized before display
- [ ] Transactions used for multi-step operations
- [ ] No raw SQL visible in error messages

### Database Patterns (Python)

```python
# GOOD - Parameterized query
cursor.execute("INSERT INTO items (name) VALUES (?)", (sanitized_name,))

# BAD - String interpolation (SQL injection risk!)
cursor.execute(f"SELECT * FROM items WHERE name = '{user_input}'")
```

---

## Error Handling

- [ ] Error messages don't expose sensitive information
- [ ] Stack traces only shown in development mode
- [ ] File paths redacted from user-facing errors
- [ ] Database details hidden from users
- [ ] Errors are logged appropriately for debugging

### Error Patterns (Python)

```python
# GOOD - Safe error handling
try:
    operation()
except Exception as e:
    logger.exception("Context")  # Full error for logs
    raise ValueError("Operation failed. Please try again.") from e  # Safe for users

# BAD - Exposing internals
except Exception as e:
    raise  # Might contain paths, SQL, etc.
```

---

## Authentication & Authorization

- [ ] Protected routes require authentication
- [ ] Sensitive operations require re-authentication
- [ ] Session tokens are not exposed in URLs
- [ ] API keys are not hardcoded or logged
- [ ] Role-based access is enforced server-side

---

## Data Protection

- [ ] Sensitive data is not stored unnecessarily
- [ ] Exports don't include internal implementation details
- [ ] PII is handled according to privacy requirements
- [ ] Data at rest is encrypted where required
- [ ] Backup files don't contain unencrypted secrets

---

## Dependencies

- [ ] `npm run audit` (pip-audit) shows no high/critical vulnerabilities
- [ ] New dependencies are from trusted sources
- [ ] Dependencies are pinned to specific versions
- [ ] No unnecessary dependencies added
- [ ] Dependency licenses are compatible

### Audit Command (this project)
```bash
npm run audit
# or: pip-audit --strict --vulnerability-service pypi
```

---

## Secrets & Configuration

- [ ] No secrets, API keys, or credentials in code
- [ ] `.gitignore` covers all sensitive files
- [ ] Environment variables used for configuration
- [ ] No hardcoded paths that should be configurable
- [ ] Production secrets are not in development configs

### Files to Check
- `.env` files (should be gitignored)
- Configuration files
- Test fixtures (may contain real data)

---

## Network Security

- [ ] HTTPS used for all external requests
- [ ] No mixed content (HTTP resources on HTTPS pages)
- [ ] CORS configured appropriately (if applicable)
- [ ] Rate limiting considered for public endpoints
- [ ] Timeouts set for external requests

---

## File System Security

- [ ] File uploads validated (type, size, content) if applicable
- [ ] Uploaded files stored outside web root if applicable
- [ ] Generated filenames don't include user input
- [ ] Temporary files are cleaned up
- [ ] File permissions are restrictive

### Path Validation Pattern (Python)
```python
# GOOD - Path traversal protection
def is_path_safe(p: Path, base: Path) -> bool:
    try:
        return p.resolve().is_relative_to(base.resolve())
    except ValueError:
        return False
```

---

## Quick Reference: Risk Levels

| Finding | Risk | Action |
|---------|------|--------|
| SQL injection possible | CRITICAL | Block ship, fix immediately |
| Secrets in code | CRITICAL | Block ship, rotate secrets |
| Path traversal possible | HIGH | Block ship, add validation |
| Missing input validation | MEDIUM | Fix before ship |
| Verbose error messages | LOW | Fix in next iteration |

---

## Sign-off

**Reviewer:** _______________  
**Date:** _______________  
**Result:** PASS / FAIL / PASS WITH NOTES

**Notes:**

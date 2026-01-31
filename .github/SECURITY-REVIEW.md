# Security Review Checklist

<!--
Copy this to: .github/SECURITY-REVIEW.md
Use this checklist when reviewing PRs that touch sensitive areas of the codebase.
-->

## Input Validation & Sanitization

- [ ] All user inputs are validated before use
- [ ] Text inputs are sanitized (HTML brackets, control characters removed)
- [ ] Email addresses are validated with proper regex
- [ ] Numeric inputs have reasonable bounds checking
- [ ] File paths are validated and don't allow directory traversal
- [ ] URL inputs are validated for allowed protocols

## Database Operations

- [ ] All queries use parameterized statements (no string concatenation)
- [ ] User inputs are never directly interpolated into SQL
- [ ] Database errors are caught and sanitized before display
- [ ] Transactions are used for multi-step operations
- [ ] Sensitive data is not logged in queries

## Error Handling

- [ ] Error messages don't expose sensitive information in production
- [ ] Stack traces are only shown in development mode
- [ ] Errors are logged appropriately (not to console in production)
- [ ] Failed operations don't leave system in inconsistent state
- [ ] Generic error messages shown to users

## Authentication & Authorization

- [ ] Sensitive operations verify user permissions
- [ ] Session/token handling follows best practices
- [ ] Password/credential handling is secure
- [ ] Rate limiting on authentication endpoints
- [ ] Proper logout/session invalidation

## Data Protection

- [ ] Sensitive data is not logged
- [ ] PII is handled according to privacy requirements
- [ ] Data exports don't leak internal implementation details
- [ ] Proper data encryption at rest/in transit
- [ ] Secure deletion of sensitive data

## API/IPC Security (if applicable)

- [ ] API endpoints validate all inputs
- [ ] Proper authentication on all endpoints
- [ ] CORS configured correctly
- [ ] Rate limiting implemented
- [ ] API responses don't expose internal errors

## Dependencies

- [ ] New dependencies are from trusted sources
- [ ] Dependencies don't have known high/critical vulnerabilities
- [ ] Dependency versions are pinned appropriately
- [ ] Minimal dependency footprint (no unnecessary packages)

## Secrets & Configuration

- [ ] No secrets, API keys, or credentials in code
- [ ] Environment variables are used for sensitive config
- [ ] `.gitignore` covers all sensitive files
- [ ] No hardcoded URLs that should be configurable
- [ ] Secrets are rotated regularly

## Common Vulnerabilities

- [ ] No XSS vulnerabilities (user content is escaped)
- [ ] No SQL injection (parameterized queries used)
- [ ] No path traversal vulnerabilities
- [ ] No insecure deserialization
- [ ] No exposure of sensitive data in URLs
- [ ] No open redirects

---

## Quick Reference

### Sanitization Functions (use these!)

```python
# Example pattern - adapt for your project
def sanitize_text(value: str, max_length: int = 1000) -> str:
    """Remove HTML and control characters."""
    import re
    if not isinstance(value, str):
        raise ValueError("Expected string")
    cleaned = re.sub(r'[<>]', '', value)
    cleaned = re.sub(r'[\x00-\x1f\x7f]', '', cleaned)
    return cleaned[:max_length].strip()

def validate_amount(value: float, min_val: float = 0, max_val: float = 1_000_000) -> None:
    """Validate numeric bounds."""
    if not isinstance(value, (int, float)) or not (-1e308 < value < 1e308):
        raise ValueError("Must be a valid number")
    if value < min_val or value > max_val:
        raise ValueError(f"Must be between {min_val} and {max_val}")
```

### Error Handling Pattern

```python
# Example pattern - adapt for your project
import logging

logger = logging.getLogger(__name__)

try:
    # operation
except Exception as error:
    logger.error("Operation failed", exc_info=True, extra={"context": "relevant info"})
    raise RuntimeError("Operation failed. Please try again.") from error
```

### Logging (not print!)

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug info", extra={"context": "value"})
logger.info("Info message", extra={"data": "value"})
logger.warn("Warning", extra={"issue": "description"})
logger.error("Error occurred", exc_info=True, extra={"context": "value"})

# Never log:
# - Passwords or credentials
# - Full credit card numbers
# - Social security numbers
# - API keys or tokens
# - Personal health information
```

### SQL Query Pattern

```python
# GOOD - Parameterized query
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))

# BAD - String concatenation (SQL injection risk!)
cursor.execute(f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')")
```

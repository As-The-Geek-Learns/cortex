# Tier 0 Setup Verification Checklist

**Date:** 2026-01-31
**Status:** VERIFIED

---

## 1.1 Install Cortex

- [x] `pip install -e .` completed successfully
- [x] Package version: `memory-context-claude-ai-0.1.0`

## 1.2 CLI Help Verification

- [x] `cortex --help` shows expected output:
  ```
  Usage: cortex <stop|precompact|session-start|reset|status|init>
  ```

## 1.3 Hook Configuration Generated

- [x] `cortex init` produces valid JSON with three hooks:
  - Stop → `cortex stop`
  - PreCompact → `cortex precompact`
  - SessionStart → `cortex session-start`

**Hook JSON (copy to Claude Code settings):**

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cortex stop"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cortex precompact"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cortex session-start"
          }
        ]
      }
    ]
  }
}
```

## 1.4 Memory Instructions Rule

- [x] `templates/cortex-memory-instructions.md` copied to `.claude/rules/cortex-memory-instructions.md`

## 1.5 CLI Commands Verified

### `cortex status`
- [x] Shows project path, hash, event count, last extraction time
- [x] Output:
  ```
  project: /Users/jamescruce/Projects/memory-context-claude-ai
  hash: 86a4d8d0dfb3b729
  events: 0
  last_extraction: none
  ```

### `cortex reset`
- [x] Completes without error
- [x] Prints confirmation: "Cortex memory reset for project ..."
- [x] Event count returns to 0 after reset

## 1.6 Test Project Created

- [x] Test project created at `~/cortex-test-project`
- [x] Git initialized on `main` branch
- [x] `cortex status` in test project:
  ```
  project: /Users/jamescruce/cortex-test-project
  hash: adf739349471d136
  events: 0
  last_extraction: none
  ```

---

## Next Steps

1. **Configure Claude Code hooks:** Add the JSON from section 1.3 to `~/.claude/settings.json` under `"hooks"`
2. **Copy memory instructions to test project:** `cp .claude/rules/cortex-memory-instructions.md ~/cortex-test-project/.claude/rules/`
3. **Proceed to Phase 2:** Manual Testing Scenarios

---

## Verification Summary

| Item | Status |
|------|--------|
| Package installed | ✅ Pass |
| CLI help works | ✅ Pass |
| `cortex init` works | ✅ Pass |
| Memory instructions copied | ✅ Pass |
| `cortex status` works | ✅ Pass |
| `cortex reset` works | ✅ Pass |
| Test project created | ✅ Pass |

**Phase 1: COMPLETE**

# Tier 0 Real-World Testing

This directory contains templates and checklists for testing the Cortex Tier 0 implementation in a real Claude Code environment.

## Testing Phases

| Phase | Description | Time Required | Status |
|-------|-------------|---------------|--------|
| **Phase 1** | Setup & Verification | 15 minutes | ✅ Complete |
| **Phase 2** | Manual Testing Scenarios | 30-60 minutes | Templates ready |
| **Phase 3** | Baseline Data Collection | 5-10 sessions (~2-5 hours) | Templates ready |
| **Phase 4** | A/B Comparison | 10 sessions (~5-10 hours) | Templates ready |
| **Phase 5** | Decay Parameter Calibration | 1-2 hours analysis | After 20+ sessions |

## Files

| File | Purpose |
|------|---------|
| [SETUP-VERIFICATION-CHECKLIST.md](SETUP-VERIFICATION-CHECKLIST.md) | Phase 1 verification results and hook configuration JSON |
| [MANUAL-TESTING-TEMPLATE.md](MANUAL-TESTING-TEMPLATE.md) | Template for Phase 2 manual testing scenarios |
| [BASELINE-DATA-TEMPLATE.md](BASELINE-DATA-TEMPLATE.md) | Template for Phase 3 baseline data collection (without Cortex) |
| [AB-COMPARISON-TEMPLATE.md](AB-COMPARISON-TEMPLATE.md) | Template for Phase 4 A/B comparison (with Cortex) |

## Quick Start

### 1. Configure Claude Code Hooks

Copy the JSON from [SETUP-VERIFICATION-CHECKLIST.md](SETUP-VERIFICATION-CHECKLIST.md) (section 1.3) to your Claude Code settings:

```bash
# Location: ~/.claude/settings.json (or project-specific settings)
# Add under "hooks" key
```

### 2. Copy Memory Instructions to Your Project

```bash
cp templates/cortex-memory-instructions.md YOUR_PROJECT/.claude/rules/
```

### 3. Run Manual Tests

Use [MANUAL-TESTING-TEMPLATE.md](MANUAL-TESTING-TEMPLATE.md) to verify single-session and multi-session behavior.

### 4. Collect Baseline Data

1. **Disable** Cortex hooks
2. Use [BASELINE-DATA-TEMPLATE.md](BASELINE-DATA-TEMPLATE.md) to record 5-10 sessions
3. Note cold start time, decision regression, and re-exploration counts

### 5. Run A/B Comparison

1. **Re-enable** Cortex hooks
2. Use [AB-COMPARISON-TEMPLATE.md](AB-COMPARISON-TEMPLATE.md) to record 10 sessions
3. Compare metrics against baseline

## Success Criteria

Per [research paper §11.4](../research/paper/cortex-research-paper.md):

| Criterion | Target |
|-----------|--------|
| Cold start time reduction | 80%+ |
| Decision regression | Near-zero |
| Plan continuity | Seamless |
| Token overhead | ≤15% of context window |
| Extraction accuracy | >90% recall |
| User maintenance effort | Near-zero |

## Test Project

A test project has been created at `~/cortex-test-project` for isolated testing:

```bash
cd ~/cortex-test-project
cortex status  # Verify Cortex recognizes the project
```

## CLI Commands for Testing

```bash
cortex status      # Show project hash, event count, last extraction
cortex reset       # Clear all events for current project
cortex init        # Print hook configuration JSON
```

## Notes

- Phases 3-5 require multiple sessions spread over days/weeks
- Use the same project for baseline and A/B comparison for fair comparison
- Record observations about briefing quality and context preservation

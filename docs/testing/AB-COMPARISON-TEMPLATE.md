# Tier 0 A/B Comparison Results

**Purpose:** Compare Cortex-enabled sessions vs. baseline sessions to measure improvement.

**Period:** YYYY-MM-DD to YYYY-MM-DD
**Project:** [Same project as baseline data collection]

---

## Instructions

1. **Re-enable Cortex hooks** in Claude Code settings (use JSON from `cortex init`)
2. Perform real development work across 10 sessions
3. For each session, record the same metrics as baseline
4. Sessions should be comparable in complexity to baseline sessions

---

## Cortex-Enabled Session Data

### Session 1 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | [Brief description] |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ (1-5) |
| **Briefing token count** | __ (estimate: `wc -c .claude/rules/cortex-briefing.md` / 4) |
| **Event count** | __ (`cortex status`) |
| **Notes** | [Observations about briefing quality, context preservation, etc.] |

---

### Session 2 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 3 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 4 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 5 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 6 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 7 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 8 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 9 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

### Session 10 (with Cortex)

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Task** | |
| **Cold start time** | __ minutes |
| **Decision regression count** | __ |
| **Re-exploration count** | __ |
| **Continuity score** | __ |
| **Briefing token count** | __ |
| **Event count** | __ |
| **Notes** | |

---

## A/B Comparison Results

| Metric | Baseline Avg | Cortex Avg | Improvement | Target | Met? |
|--------|-------------|-----------|-------------|--------|------|
| Cold start time (min) | | | % reduction | 80%+ | [ ] |
| Decision regression | | | % reduction | Near-zero | [ ] |
| Re-exploration count | | | % reduction | Significant | [ ] |
| Continuity score (1-5) | | | + points | Improvement | [ ] |
| Token overhead | N/A | | % of context | ≤15% | [ ] |

---

## Success Criteria Evaluation

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
| Cold start time reduction | 80%+ | | [ ] Pass [ ] Fail |
| Decision regression | Near-zero | | [ ] Pass [ ] Fail |
| Plan continuity | Seamless | | [ ] Pass [ ] Fail |
| Token overhead | ≤15% | | [ ] Pass [ ] Fail |
| Extraction accuracy | >90% recall | | [ ] Pass [ ] Fail |
| User maintenance effort | Near-zero | | [ ] Pass [ ] Fail |

---

## Qualitative Observations

### Briefing Quality

[How useful was the briefing content? Did it include the right information?]

### Context Preservation

[Did Claude remember decisions, plans, and prior work?]

### Pain Points

[Any issues with Cortex? Missing events? Wrong information?]

### Unexpected Benefits

[Any positive surprises? Things that worked better than expected?]

---

## Conclusion

**Overall Assessment:** [ ] Tier 0 meets success criteria [ ] Needs iteration

**Recommendation:**
- [ ] Proceed to Tier 1 implementation
- [ ] Iterate on Tier 0 (specify areas)
- [ ] Gather more data before deciding

**Key Learnings:**

[Summarize what was learned from the A/B comparison]

---

## Appendix: Sample Briefings

### Briefing from Session 5

```markdown
[Paste a representative briefing here]
```

### Briefing from Session 10

```markdown
[Paste the final briefing here]
```

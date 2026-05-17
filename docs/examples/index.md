# Examples

These examples are designed to be copied, adapted, and used as a starting point for your own controls. Each one is a complete, runnable YAML block — drop it straight into a `controls:` list.

The examples are grouped by complexity:

| Page | Engine | What you'll learn |
|---|---|---|
| [Easy examples](easy.md) | `pandas_query` | Filtering rows, comparing scalars, writing assertion messages |
| [Hard examples](hard.md) | `python` | Multi-DataFrame joins, conditional logic, REVIEW and SKIP verdicts |

---

## Which engine should I use?

```
Can the whole check be expressed as a single filter?
  YES → pandas_query  (simpler, less to write)
  NO  → python        (full flexibility)
```

A "single filter" means: apply one `DataFrame.query()` expression; if any rows survive, that's a failure. That covers a surprisingly large number of real-world controls.

You need the `python` engine when:

- The check spans more than one DataFrame (e.g. STARTED profiles → userid → PROTECTED flag)
- The verdict depends on conditional logic (if X then check Y, else check Z)
- You need to produce a REVIEW verdict instead of a binary PASS/FAIL
- A required data source might not be present and the control should SKIP gracefully

---

## Anatomy of a control (quick recap)

```yaml
controls:
  - control_id: CUSTOM-EXAMPLE        # stable unique ID — never reuse or rename
    title: "Human-readable name"       # shown as the heading in the report
    severity: high                     # high / medium / low — drives report coloring
    custom:                            # citation block — use 'cis:' for CIS standards
      benchmark: "Internal policy"
      category:  "Section name in report"
    data_sources_needed: [irrdbu00]    # tells the runner which files are required
    implementation:
      engine: pandas_query             # or: python
      # ... engine-specific fields ...
    remediation: >
      What an admin should do to fix this finding.
```

Every field is required. The `remediation` text appears in the report under each failing control — write it as a concrete command, not vague advice.

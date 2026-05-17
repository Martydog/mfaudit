# MFAudit

**Automated RACF security auditing — from raw data exports to a styled report in one command.**

MFAudit reads the runtime exports that every z/OS system can produce — an IRRDBU00 unload and a SETROPTS REXX export — and evaluates them against a library of security controls drawn from the CIS z/OS Benchmarks. The result is a PDF report, a CSV of all findings, and a clear pass/fail/review verdict for every control.

**[Full documentation → mfaudit.readthedocs.io](https://mfaudit.readthedocs.io/)**

---

## What you get

| | |
|---|---|
| **46 CIS controls** | Password policy, class activation, STARTED tasks, Unix System Services, Db2, CICS |
| **Custom controls** | Write your own shop-specific rules in YAML with the same engine |
| **Anonymized reports** | Replace all user/group/profile names with stable labels before sharing externally |

---

## Quick start

```bash
# 1  Install
pip install mfaudit                  # includes WeasyPrint for PDF output

# 2  Get the controls library
git clone https://github.com/wizardofzos/mfaudit.git
cd mfaudit

# 3  Run (outputs land in current directory by default)
mfaudit --irrdbu00 /path/to/IRRDBU00 \
        --setropts  /path/to/SETROPTS \
        --controls  controls.yaml

# 4  Open
open report.pdf
```

---

## Repository layout

```
controls.yaml            46 CIS Benchmark controls (z/OS, Db2, CICS)
example_controls.yaml     Example custom controls
mfaudit/                 Installed Python package (CLI entry point: mfaudit)
docs/                    MkDocs documentation (readthedocs.io)
```

---

## Writing your own controls

Controls are YAML. Every control names the exact mfpandas DataFrame and column(s) it uses.

```yaml
controls:
  - control_id: CUSTOM-NO-DUAL-PRIVS
    title: "No active user may hold both SPECIAL and OPERATIONS"
    severity: high
    custom:
      benchmark: "Internal policy"
      category:  "Privileged access"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: python
      dataset: irrdbu00.users
      select_columns: [USBD_NAME, USBD_SPECIAL, USBD_OPER]
      logic: |
        hits = df[
            (df['USBD_SPECIAL'] == 'YES') &
            (df['USBD_OPER'] == 'YES') &
            (df['USBD_REVOKE'] != 'YES')
        ]
        status = 'FAIL' if not hits.empty else 'PASS'
        detail = f"{len(hits)} user(s) hold both SPECIAL and OPERATIONS"
        findings = hits.to_dict('records')
    remediation: "ALTUSER <userid> NOSPECIAL  or  ALTUSER <userid> NOOPER"
```

Two engines are available:

| Engine | Use when |
|---|---|
| `pandas_query` | Single filter expression; empty result = PASS |
| `python` | Multi-DataFrame logic, conditional branching, per-row decisions |

See the **[Authoring controls](https://mfaudit.readthedocs.io/authoring/)** documentation for the full schema and Python engine variable reference.

---

## Data sources

| Source | mfpandas class | How to collect |
|---|---|---|
| `--setropts` | `SETROPTS` | REXX/IRRXUTIL export (KEY:VALUE format) |
| `--irrdbu00` | `IRRDBU00` | IRRDBU00 batch utility unload |
| `--dcollect` | `DCOLLECT` | IDCAMS DCOLLECT output (optional) |

Detailed collection instructions are in the **[Quick start guide](https://mfaudit.readthedocs.io/quickstart/)**.

---

## Requirements

- Python 3.9 or later
- `pip install mfaudit` — installs all dependencies including WeasyPrint for PDF output
- For pure-Python PDF fallback: `pip install "mfaudit[pdf-xhtml]"` adds xhtml2pdf

---

## Disclaimer

All findings must be validated by a qualified RACF security administrator before remediation. REVIEW-status items require human judgment and cannot be automatically determined compliant or non-compliant.

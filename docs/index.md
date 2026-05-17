<p align="center">
  <img src="images/mfaudit-logo.png" alt="MFAudit logo" width="320">
</p>

# MFAudit

**Automated RACF security auditing — from raw data exports to a styled report in one command.**

MFAudit reads the runtime exports that every z/OS system can produce — an IRRDBU00 unload and a SETROPTS REXX export — and evaluates them against a library of security controls drawn from the CIS z/OS Benchmarks. The result is a paginated HTML/PDF report, a CSV of all findings, and a clear pass/fail/review verdict for every control.

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
# 1  Collect data on z/OS (see Getting started → Quick start for REXX)
#    Copy SETROPTS and IRRDBU00 to your workstation

# 2  Install
pip install mfaudit

# 3  Clone the repo to get the controls library
git clone https://github.com/wizardofzos/mfaudit.git
cd mfaudit

# 4  Run (outputs land in current directory by default)
mfaudit --controls controls.yaml

# 5  Open the report
open report.pdf             # macOS
xdg-open report.pdf         # Linux
```

Defaults: `--setropts ./SETROPTS` and `--irrdbu00 ./IRRDBU00`.  
Controls that need a missing data source are automatically marked **SKIP**.

---

## Data flow

```
z/OS system
  ├── IRRDBU00 unload  ──────────────────────────────────┐
  └── SETROPTS REXX export  ───────────────────────────┐ │
                                                        ↓ ↓
  controls.yaml  ──────────────────────────►  mfaudit
  example_controls.yaml (optional)  ────────►     │
                                                  ↓
                                         out/report.pdf
                                         out/controls_results.csv
```

---

## Repository layout

```
controls.yaml            46 CIS Benchmark controls (z/OS, Db2, CICS)
example_controls.yaml     Example custom controls
mfaudit/                 Installed Python package (CLI entry point: mfaudit)
docs/                    This documentation (MkDocs)
```

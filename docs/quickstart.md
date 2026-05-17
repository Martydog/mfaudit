# Quick start

This page walks you through your first MFAudit run — from collecting data on the mainframe to opening the finished report.

---

## Step 1 — Collect data on z/OS

You need two files from the mainframe:

| File | What it contains |
|---|---|
| `IRRDBU00` | Full RACF database unload (users, groups, profiles, access lists) |
| `SETROPTS` | RACF global option export (password rules, active classes, flags) |

### IRRDBU00 unload

Submit the IRRDBU00 batch utility. A minimal JCL example:

```jcl
//RACFUNLD JOB  CLASS=A,MSGCLASS=X
//STEP1    EXEC PGM=IRRDBU00,PARM='NOLOCKINPUT'
//SYSPRINT DD   SYSOUT=*
//INDD1    DD   DSN=SYS1.RACF,DISP=SHR       ← your RACF database
//OUTDD1   DD   DSN=&&UNLOAD,DISP=(NEW,PASS),
//             UNIT=SYSDA,SPACE=(CYL,(50,10))
//SYSIN    DD   DUMMY
```

Copy the output dataset to your workstation as a binary file.

### SETROPTS REXX export

MFAudit requires a **REXX-produced** SETROPTS export — not raw `SETROPTS LIST` console output. Run this REXX exec on the mainframe:

```rexx
/* REXX — export SETROPTS settings as KEY:VALUE lines */
"SETROPTS LIST"
parse value "" with output
do queued()
  pull line
  output = output || line || '0A'x
end
address MVS "EXECIO * DISKW SETROPTS (STEM output. FINIS)"
```

The exec writes one `KEY:VALUE` line per setting. Copy `SETROPTS` to your workstation as text.

---

## Step 2 — Install MFAudit

```bash
pip install mfaudit
```

WeasyPrint is included automatically — PDF output works out of the box on most systems. See [Installation](installation.md) for required system libraries.

Then clone the repository to get the controls library:

```bash
git clone https://github.com/wizardofzos/mfaudit.git
cd mfaudit
```

See [Installation](installation.md) for PDF system dependencies and development setup.

---

## Step 3 — Run the audit

Place `IRRDBU00` and `SETROPTS` in the project root (or pass paths explicitly).

**Minimal run — output written to current directory:**

```bash
mfaudit --controls controls.yaml
```

**With explicit file paths, metadata, and output directory:**

```bash
mfaudit --irrdbu00 /data/IRRDBU00 \
        --setropts  /data/SETROPTS \
        --controls  controls.yaml \
        --system-name SYSA \
        --report-date 2026-05-17 \
        --out out/
```

---

## Step 4 — Open the report

```bash
open out/report.pdf         # macOS
xdg-open out/report.pdf     # Linux
start out\report.pdf        # Windows
```

CSV findings are in `out/controls_results.csv` (or the current directory if `--out` was not used).

---

## What you see on the console

```
[+] Loaded 46 control(s) from controls.yaml
[+] Total: 46 control(s)

[+] Parsing SETROPTS ...
[+] Parsing IRRDBU00 ...

[CIS-1.1.1] Ensure PASSWORD(INTERVAL) is set to no longer than 90 days  PASS
[CIS-1.1.2] Ensure PASSWORD(HISTORY) is set to at least 4              PASS
[CIS-1.2.5] Ensure started tasks defined with TRUSTED attribute ...     REVIEW  (3 findings)
...

[+] PDF  written to out/report.pdf  (engine: WeasyPrint)
[+] CSV  written to out/controls_results.csv
```

Controls that cannot run because a data source is missing are marked **SKIP** automatically — they do not count as failures.

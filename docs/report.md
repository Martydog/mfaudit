# Report output

`mfaudit` writes two output files after every run. By default both land in the current directory; use `--out DIR` to choose a different location.

---

## PDF report — `report.pdf`

The primary output. Open it in any PDF viewer.

### Structure

**Cover page**

- System name and report date
- Summary counts: total controls, PASS / FAIL / REVIEW / SKIP / ERROR
- Overall risk rating

**Per-benchmark sections**

Controls are grouped by source:

- CIS IBM z/OS Benchmark
- CIS IBM Db2 13 Benchmark
- CIS IBM CICS Benchmark
- Custom controls

Each section lists controls in order with:

| Column | Content |
|---|---|
| ID | Control identifier |
| Title | Short description |
| Severity | `HIGH` / `MEDIUM` / `LOW` badge |
| Status | `PASS` / `FAIL` / `REVIEW` / `SKIP` / `ERROR` badge |
| Detail | One-line summary |

**Finding detail**

FAIL and REVIEW controls expand to show the raw finding rows — the actual RACF records that triggered the verdict. Column names are the mfpandas DataFrame column names.

### PDF library installation

WeasyPrint is installed automatically with `pip install mfaudit` and is the preferred PDF engine. It requires a small set of native system libraries:

=== "macOS"

    ```bash
    brew install pango cairo gobject-introspection
    ```

=== "Debian / Ubuntu"

    ```bash
    sudo apt-get install -y \
        libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libcairo2 libffi-dev shared-mime-info
    ```

=== "Windows"

    Install the [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
    and add its `bin` directory to `PATH`.

    Or skip WeasyPrint and use xhtml2pdf — no extra native libraries needed:
    `pip install "mfaudit[pdf-xhtml]"`

If WeasyPrint is unavailable, MFAudit automatically falls back to xhtml2pdf (if installed via `pip install "mfaudit[pdf-xhtml]"`).

---

## CSV — `controls_results.csv`

One row per control. Useful for importing into spreadsheets, dashboards, or ticketing systems.

| Column | Content |
|---|---|
| `control_id` | Stable control identifier |
| `title` | Control title |
| `severity` | `high` / `medium` / `low` |
| `status` | `PASS` / `FAIL` / `REVIEW` / `SKIP` / `ERROR` |
| `detail` | One-line verdict summary |
| `data_sources` | Comma-separated list of required sources |
| `benchmark` | Source benchmark name |

---

## Anonymized reports

Pass `--anonymize` to replace all RACF user IDs, group names, and profile names with stable pseudonymous labels (`USR-0001`, `GRP-0042`, etc.) before writing output. The mapping is deterministic within a single run — the same name always gets the same label, so findings remain interpretable.

```bash
mfaudit --controls controls.yaml --anonymize --out out/
```

Useful when sharing reports with external auditors or vendors without disclosing internal naming conventions.

---

## Customizing the report

### Bundled templates

Two templates ship with MFAudit:

| Template | Style |
|---|---|
| `templates/default-report.html.j2` | Light corporate theme — the default |
| `templates/terminal-report.html.j2` | Dark phosphor-green 3270-style terminal theme |

Use the terminal theme by short name:

```bash
mfaudit --controls controls.yaml --template terminal
```

See all available names:

```bash
mfaudit --list-templates
```

Or point at any local `.html.j2` file you have written or edited:

```bash
mfaudit --controls controls.yaml --template /path/to/my-report.html.j2
```

### Writing your own template

The template is a standard Jinja2 HTML file rendered to a string, then handed to WeasyPrint. All styles should be inline (`<style>` in `<head>`) so there is no external CSS dependency.

The following variables are available in every template:

| Variable | Type | Content |
|---|---|---|
| `system_name` | str | Value of `--system-name` |
| `report_date` | str | Value of `--report-date` (or today) |
| `generated_at` | str | Timestamp of the run |
| `controls_file` | str | Controls file(s) used |
| `total` | int | Total control count |
| `passed` / `failed` / `review` / `skipped` / `errors` | int | Per-status counts |
| `score_pct` | int | `passed / (total - skipped) × 100` |
| `results` | list | One dict per control (see below) |
| `sections` | dict | Results grouped by section/category |
| `anonymized` | bool | True if `--anonymize` was passed |
| `STATUS_PASS` … `STATUS_ERROR` | str | Status string constants |

Each entry in `results` has: `control_id`, `title`, `cis_section`, `cis_level`, `custom_benchmark`, `custom_category`, `custom_reference`, `severity`, `requirement`, `remediation`, `data_sources_needed`, `status`, `detail`, `findings` (list of dicts).

Start from one of the bundled templates and modify to taste.

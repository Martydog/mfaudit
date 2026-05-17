# Contributing

MFAudit is open source under the AGPL v3 license and contributions are very welcome.
The two areas where help is most needed right now are **STIG controls** and **report templates** —
but any improvement is appreciated.

---

## Where to start

| Area | What's needed | Skills |
|---|---|---|
| [STIG controls](#stig-controls) | DISA STIG rules for z/OS RACF translated into MFAudit YAML | RACF knowledge + YAML |
| [Report templates](#report-templates) | New Jinja2 HTML themes for the PDF report | HTML + CSS |
| Bug fixes / improvements | Anything in the issue tracker | Python |
| Documentation | Corrections, examples, clearer explanations | Writing |

---

## STIG controls

The CIS z/OS Benchmark covers a solid baseline, but many shops are required to comply with
[DISA STIG V8R12 for z/OS RACF](https://public.cyber.mil/stigs/). We would love a community-maintained
`stig_controls.yaml` file that brings those rules into MFAudit.

**What a STIG control looks like:**

```yaml
controls:
  - control_id: STIG-RACF-001
    title: "RACF must be configured to protect the SMF data sets"
    severity: high
    custom:
      benchmark: "DISA STIG z/OS RACF V8R12"
      category:  "Audit and Accountability"
      reference: "RACF-001"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: pandas_query
      dataset: irrdbu00.datasets
      select_columns: [DSBD_NAME, DSBD_UACC]
      filter: "DSBD_NAME.str.startswith('SYS1.MAN') and DSBD_UACC != 'NONE'"
      assertion:
        type: no_rows
        pass_message: "SMF datasets are protected"
        fail_message: "{n} SMF dataset profile(s) with UACC other than NONE"
    remediation: >
      ALTDSD 'SYS1.MAN*' UACC(NONE)
```

See the [Authoring controls](authoring/index.md) documentation for the full schema and
available DataFrames. The [examples](examples/easy.md) show common patterns.

---

## Report templates

MFAudit ships with two templates (`default` and `terminal`). More themes would be a great
addition — a light high-contrast accessibility theme, a branded corporate template, or a
minimal black-and-white print theme are all ideas worth exploring.

**What a template needs:**

- A single `.html.j2` file using Jinja2 syntax
- All CSS inline in `<head>` — no external dependencies
- Render correctly as a PDF via WeasyPrint (`-webkit-print-color-adjust: exact`)
- Use the [template variables](report.md#writing-your-own-template) already available

Drop the file in `mfaudit/templates/` and it is immediately usable via `--template <name>`.

See the existing templates in
[`mfaudit/templates/`](https://github.com/wizardofzos/mfaudit/tree/main/mfaudit/templates)
as a starting point.

---

## Development setup

```bash
git clone git@github.com:wizardofzos/mfaudit.git
cd mfaudit
python -m venv .venv
source .venv/bin/activate
pip install -e ".[docs]"
```

Run the docs locally:

```bash
mkdocs serve
```

---

## Submitting a contribution

1. Fork the repository on GitHub
2. Create a branch: `git checkout -b my-contribution`
3. Make your changes
4. Open a pull request against `main` with a short description of what you changed and why

For STIG controls, include a reference to the specific STIG rule ID in the `reference` field
so findings can be traced back to the source requirement.

---

## License

By contributing you agree that your code will be released under the same
[AGPL v3 license](https://www.gnu.org/licenses/agpl-3.0.html) as the rest of the project.

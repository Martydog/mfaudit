# Controls overview

MFAudit evaluates security controls expressed in YAML. Every control maps to one or more mfpandas DataFrames, runs a query or Python logic, and produces a deterministic verdict.

---

## Control libraries

| File | Controls | Source |
|---|---|---|
| `controls.yaml` | 46 | CIS IBM z/OS, Db2, and CICS Benchmarks |
| `example_controls.yaml` | yours | Your own shop-specific rules |

Multiple files can be merged at runtime:

```bash
mfaudit --controls controls.yaml example_controls.yaml --out out/
```

---

## Execution engines

### `pandas_query`

An optional `filter` expression is applied to the target DataFrame via pandas `.query()`, then an `assertion` block determines the verdict. Two assertion types are supported:

**`no_rows`** — PASS when the filtered result is empty; each surviving row is a finding.

```yaml
implementation:
  engine: pandas_query
  dataset: irrdbu00.datasets
  select_columns: [DSBD_NAME, DSBD_UACC]
  filter: "DSBD_UACC == 'ALTER'"
  assertion:
    type: no_rows
    pass_message: "No dataset profiles with UACC=ALTER"
    fail_message: "Dataset profile(s) found with UACC=ALTER"
```

**`scalar_compare`** — reads the `Value` column of the first filtered row and compares it to `expected` using `operator`. `{value}` in messages is replaced with the actual value.

```yaml
implementation:
  engine: pandas_query
  dataset: setropts.fieldInfo
  select_columns: [Setting, Value]
  filter: "Setting == 'INTERVAL'"
  assertion:
    type: scalar_compare
    operator: "<="
    expected: 90
    pass_message: "PASSWORD INTERVAL is {value} days (≤ 90)"
    fail_message: "PASSWORD INTERVAL exceeds 90 days (value: {value})"
```

Supported operators: `<=`, `>=`, `<`, `>`, `==`, `!=`.

Use `pandas_query` when the test is a single filter + assertion. Use `python` for anything more complex.

See the [full schema](../authoring/schema.md) for all assertion fields and defaults.

### `python`

Arbitrary Python logic runs with the full mfpandas namespace injected. The logic block must set `status` (`'PASS'`, `'FAIL'`, `'REVIEW'`, `'SKIP'`) and optionally `detail` (string) and `findings` (list of dicts).

```yaml
implementation:
  engine: python
  dataset: irrdbu00.users
  select_columns: [USBD_NAME, USBD_NOPWD]
  logic: |
    row = df[df['USBD_NAME'].str.upper() == 'MYSVC']
    if len(row) == 0:
        status = 'FAIL'
        detail = "STC userid MYSVC not found"
        findings = [{'USBD_NAME': 'MYSVC', 'status': 'NOT DEFINED'}]
    else:
        nopwd = row['USBD_NOPWD'].values[0]
        status = 'PASS' if nopwd == 'YES' else 'FAIL'
        detail = f"NOPASSWORD={nopwd}"
        findings = row.to_dict('records')
```

Available variables in `logic`:

| Variable | Type | Content |
|---|---|---|
| `df` | DataFrame | The dataset named in `dataset` |
| `users_df` | DataFrame | `irrdbu00.users` |
| `omvs_df` | DataFrame | `irrdbu00.userOMVS` |
| `groups_df` | DataFrame | `irrdbu00.groups` |
| `gomvs_df` | DataFrame | `irrdbu00.groupOMVS` |
| `access_df` | DataFrame | `irrdbu00.generalAccess` |
| `setropts` | object | Full SETROPTS object |
| `irrdbu00` | object | Full IRRDBU00 object |
| `dcollect` | object | Full DCOLLECT object (or `None`) |
| `pd` | module | pandas |

---

## Status values

| Status | Meaning |
|---|---|
| **PASS** | All assertions satisfied |
| **FAIL** | One or more findings; detail and rows shown in report |
| **REVIEW** | Human judgment needed (e.g., list of TRUSTED accounts to validate) |
| **SKIP** | Required data source not supplied; not counted as a failure |
| **ERROR** | Control logic raised an exception |

---

## Data sources

| Key | mfpandas object | Loaded from |
|---|---|---|
| `setropts` | `SETROPTS` | `--setropts` argument |
| `irrdbu00` | `IRRDBU00` | `--irrdbu00` argument |
| `dcollect` | `DCOLLECT` | `--dcollect` argument (optional) |

Controls declare which sources they need:

```yaml
data_sources_needed: [setropts, irrdbu00]
```

If any required source is absent, the control is automatically marked **SKIP**.

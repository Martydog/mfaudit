# Full YAML schema

A controls YAML file has one top-level key `controls:` containing a list of control objects.

```yaml
controls:
  - <control>
  - <control>
```

---

## Control object

```yaml
- control_id: <string>           # required — unique stable identifier
  title: <string>                # required — short human-readable name
  severity: high | medium | low  # required — used for report coloring and sorting
  <citation-block>               # required — one of: cis, custom
  data_sources_needed:           # required — list of: setropts, irrdbu00, dcollect
    - setropts
    - irrdbu00
  implementation:                # required
    <implementation-block>
  remediation: <string>          # required — what to do when the control fails
```

---

## Citation blocks

Exactly one of the following is required. They are mutually exclusive.

### `cis:` block

```yaml
cis:
  section: <string>    # e.g. "1.1.1"
  level: L1 | L2
  benchmark: <string>  # e.g. "CIS z/OS 2.5.0"
```

### `custom:` block

```yaml
custom:
  benchmark: <string>  # e.g. "Internal policy" or regulation name
  category:  <string>  # section label shown in the report
  reference: <string>  # optional — internal policy reference
```

---

## Implementation block — `pandas_query` engine

```yaml
implementation:
  engine: pandas_query
  dataset: <dotted-path>        # e.g. setropts.fieldInfo, irrdbu00.users
  select_columns: [<col>, ...]  # columns shown in findings rows
  filter: <pandas-query-string> # passed to DataFrame.query() before assertion
  assertion:
    type: <assertion-type>      # see below
    ...
```

**`filter`** is a pandas `.query()` expression string applied to the dataset before the assertion is evaluated. Column names with spaces must be backtick-quoted: `` `Column Name` ``. String comparisons are case-sensitive by default. `filter` may be omitted — the entire DataFrame is then passed to the assertion.

**`assertion`** is a YAML mapping. Three types are supported:

---

### Assertion type: `no_rows`

Pass when the filtered DataFrame is empty. Each surviving row is a finding.

```yaml
assertion:
  type: no_rows
  pass_message: "No violations found"          # optional
  fail_message: "N finding(s) returned"        # optional; N is the row count
```

Both messages are optional. Default `pass_message` is `"No violations"`.
Default `fail_message` is `"<N> finding(s)"` where N is the actual row count.

**Example** — ensure no dataset profile has UACC=ALTER:

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

---

### Assertion type: `scalar_compare`

Filter must return at least one row. The `Value` column of the first row is read,
coerced to `int` if possible, then compared against `expected` using `operator`.

```yaml
assertion:
  type: scalar_compare
  operator: "<="          # one of: <= >= > < == !=
  expected: 90            # int or string to compare against
  pass_message: "PASSWORD INTERVAL is {value} days (≤ 90)"
  fail_message: "PASSWORD INTERVAL exceeds 90 days (value: {value})"
```

`{value}` in either message is replaced with the actual value read from the row.

If the filtered DataFrame is empty (setting not found), the control returns **FAIL**
with detail `"Setting not found in data"`.

**Example** — ensure PASSWORD INTERVAL ≤ 90 days:

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

Supported operators:

| Operator | Meaning |
|---|---|
| `<=` | actual ≤ expected |
| `>=` | actual ≥ expected |
| `<`  | actual < expected |
| `>`  | actual > expected |
| `==` | actual == expected |
| `!=` | actual != expected |

---

### Assertion type: `python_result`

Used alongside the **`python` engine** (not `pandas_query`). The assertion block is documentation-only — it describes what PASS and FAIL mean, but the verdict is determined entirely by the `logic` block.

```yaml
implementation:
  engine: python
  dataset: irrdbu00.users
  select_columns: [USBD_NAME, USBD_NOPWD]
  assertion:
    type: python_result
    pass_message: "STC userid is PROTECTED"
    fail_message: "STC userid is not PROTECTED or does not exist"
  logic: |
    row = df[df['USBD_NAME'].str.upper() == 'SDSF']
    if row.empty:
        status = 'FAIL'
        detail = "STC userid SDSF not found"
    else:
        nopwd = row['USBD_NOPWD'].values[0]
        status = 'PASS' if nopwd == 'YES' else 'FAIL'
        detail = f"NOPASSWORD={nopwd}"
        findings = row.to_dict('records')
```

The `pass_message` / `fail_message` values serve as human-readable documentation of intent. They are not used at runtime.

---

## Implementation block — `python` engine

```yaml
implementation:
  engine: python
  dataset: <dotted-path>           # primary DataFrame, exposed as `df`
                                   # or combined specs: "irrdbu00.users + irrdbu00.groups"
  select_columns: [<col>, ...]     # informational; shown in report header
  assertion:
    type: python_result            # optional — documentation only
    pass_message: "..."
    fail_message: "..."
  logic: |
    # Python code block
    # Must set: status (str)
    # May set:  detail (str), findings (list of dicts)
```

### Combined `dataset` specs

When a control needs more than one DataFrame, join them with ` + `:

```yaml
dataset: "irrdbu00.userOMVS + irrdbu00.users"
```

Each component is exposed under a fixed variable name:

| Component in `dataset` | Variable in `logic` |
|---|---|
| `irrdbu00.users` | `users_df` |
| `irrdbu00.userOMVS` | `omvs_df` |
| `irrdbu00.groups` | `groups_df` |
| `irrdbu00.groupOMVS` | `gomvs_df` |
| `irrdbu00.generalAccess` | `access_df` |
| any other spec | `df` |

Single-spec `dataset` values are always exposed as `df`.

### Variables injected into `logic`

These are available regardless of which `dataset` is specified:

| Name | Type | Value |
|---|---|---|
| `df` | `pd.DataFrame` | The primary DataFrame (single `dataset` spec) |
| `users_df` | `pd.DataFrame` | `irrdbu00.users` (combined spec or always available via `irrdbu00.users`) |
| `omvs_df` | `pd.DataFrame` | `irrdbu00.userOMVS` (combined spec) |
| `groups_df` | `pd.DataFrame` | `irrdbu00.groups` (combined spec) |
| `gomvs_df` | `pd.DataFrame` | `irrdbu00.groupOMVS` (combined spec) |
| `access_df` | `pd.DataFrame` | `irrdbu00.generalAccess` (combined spec) |
| `setropts` | `SETROPTS` | Full SETROPTS object |
| `irrdbu00` | `IRRDBU00` | Full IRRDBU00 object (access any DataFrame via `irrdbu00.generals` etc.) |
| `dcollect` | `DCOLLECT` \| `None` | Full DCOLLECT object, or `None` if not loaded |
| `pd` | module | pandas |

### Variables the `logic` block must set

| Name | Type | Required | Description |
|---|---|---|---|
| `status` | `str` | **yes** | `'PASS'`, `'FAIL'`, `'REVIEW'`, or `'SKIP'` |
| `detail` | `str` | no | One-line summary shown under the verdict |
| `findings` | `list[dict]` | no | Rows shown in the findings table |

If `logic` raises an exception, the control is marked **ERROR** and the traceback appears in the console output.

---

## Dataset dotted-path reference

| Path | Object | DataFrame |
|---|---|---|
| `setropts.fieldInfo` | SETROPTS | Global SETROPTS key/value settings |
| `setropts.classInfo` | SETROPTS | Per-class activation flags |
| `irrdbu00.users` | IRRDBU00 | User base records (0200) |
| `irrdbu00.groups` | IRRDBU00 | Group base records (0100) |
| `irrdbu00.userOMVS` | IRRDBU00 | User OMVS segments (0270) |
| `irrdbu00.groupOMVS` | IRRDBU00 | Group OMVS segments (0170) |
| `irrdbu00.connectData` | IRRDBU00 | User-to-group connections (0205) |
| `irrdbu00.generals` | IRRDBU00 | General resource base records (0500) |
| `irrdbu00.generalSTDATA` | IRRDBU00 | General resource STDATA segments (0503) |
| `irrdbu00.generalAccess` | IRRDBU00 | General resource access lists (0510) |
| `irrdbu00.datasets` | IRRDBU00 | Dataset base records (0400) |
| `irrdbu00.datasetAccess` | IRRDBU00 | Dataset access lists (0410) |
| `dcollect.datasets` | DCOLLECT | Dataset catalog entries |

---

## Complete example

```yaml
controls:
  - control_id: CIS-1.1.1
    title: "Ensure PASSWORD(INTERVAL) is set to no longer than 90 days"
    severity: medium
    cis:
      section: "1.1.1"
      level: L1
      benchmark: "CIS z/OS RACF Benchmark"
    data_sources_needed: [setropts]
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
    remediation: >
      Set the password expiry interval: SETROPTS PASSWORD(INTERVAL(90))
```

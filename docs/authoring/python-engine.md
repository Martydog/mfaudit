# Python engine

Use the `python` engine when the test cannot be expressed as a single `DataFrame.query()` call: multi-DataFrame lookups, conditional branching, per-row decisions, or complex aggregations.

---

## Anatomy of a `logic` block

```yaml
implementation:
  engine: python
  dataset: irrdbu00.users        # loaded as `df`
  select_columns: [USBD_NAME, USBD_NOPWD]
  assertion:                     # optional — documents intent, not enforced at runtime
    type: python_result
    pass_message: "STC userid is PROTECTED"
    fail_message: "STC userid is not PROTECTED or does not exist"
  logic: |
    # Your Python here.
    # Must assign `status`.
    # Optionally assign `detail` and `findings`.
    row = df[df['USBD_NAME'].str.upper() == 'MYSVC']
    if row.empty:
        status = 'FAIL'
        detail = "STC userid MYSVC not found in RACF database"
        findings = [{'USBD_NAME': 'MYSVC', 'USBD_NOPWD': 'NOT DEFINED'}]
    else:
        nopwd = row['USBD_NOPWD'].values[0]
        status = 'PASS' if nopwd == 'YES' else 'FAIL'
        detail = f"MYSVC NOPASSWORD={nopwd}"
        findings = row[['USBD_NAME', 'USBD_NOPWD']].to_dict('records')
```

The `assertion` block with `type: python_result` is documentation-only — it describes what PASS and FAIL mean, but the verdict is entirely determined by what your `logic` block assigns to `status`. It is good practice to include it so the YAML is self-describing.

---

## Multi-DataFrame `dataset` specs

When a control needs more than one DataFrame, join the specs with ` + `:

```yaml
dataset: "irrdbu00.userOMVS + irrdbu00.users"
```

Each component is exposed under a fixed variable name in `logic`:

| Component | Variable |
|---|---|
| `irrdbu00.users` | `users_df` |
| `irrdbu00.userOMVS` | `omvs_df` |
| `irrdbu00.groups` | `groups_df` |
| `irrdbu00.groupOMVS` | `gomvs_df` |
| `irrdbu00.generalAccess` | `access_df` |
| any other spec | `df` |

Example — check that every UID 0 user is PROTECTED:

```yaml
dataset: "irrdbu00.userOMVS + irrdbu00.users"
logic: |
    uid0 = omvs_df[omvs_df['USOMVS_UID'] == 0]
    bad = []
    for _, row in uid0.iterrows():
        name = row['USOMVS_NAME']
        user = users_df[users_df['USBD_NAME'] == name]
        if user.empty or user['USBD_NOPWD'].values[0] != 'YES':
            bad.append({'USOMVS_NAME': name, 'USOMVS_UID': 0, 'USBD_NOPWD': 'NO'})
    status = 'FAIL' if bad else 'PASS'
    detail = f"{len(bad)} UID 0 account(s) are not PROTECTED" if bad else "All UID 0 accounts are PROTECTED"
    findings = bad
```

For single-spec `dataset` values, the DataFrame is always `df`.

---

## Available variables

| Variable | Type | Content |
|---|---|---|
| `df` | `pd.DataFrame` | The DataFrame named in `dataset` (single spec) |
| `users_df` | `pd.DataFrame` | `irrdbu00.users` |
| `omvs_df` | `pd.DataFrame` | `irrdbu00.userOMVS` |
| `groups_df` | `pd.DataFrame` | `irrdbu00.groups` |
| `gomvs_df` | `pd.DataFrame` | `irrdbu00.groupOMVS` |
| `access_df` | `pd.DataFrame` | `irrdbu00.generalAccess` |
| `setropts` | object | Full SETROPTS object with `.fieldInfo`, `.classInfo` |
| `irrdbu00` | object | Full IRRDBU00 object with all DataFrames as attributes |
| `dcollect` | object \| `None` | DCOLLECT object, or `None` if `--dcollect` was not supplied |
| `pd` | module | pandas |

Access any DataFrame directly from the objects:

```python
all_generals = irrdbu00.generals
all_datasets  = irrdbu00.datasets
class_info    = setropts.classInfo
```

---

## Output variables

| Variable | Required | Type | Notes |
|---|---|---|---|
| `status` | **yes** | `str` | `'PASS'`, `'FAIL'`, `'REVIEW'`, or `'SKIP'` |
| `detail` | no | `str` | One-line summary shown below the verdict in the report |
| `findings` | no | `list[dict]` | Each dict becomes a row in the findings table |

If `logic` exits without setting `status`, the control is marked **ERROR**.

---

## Common patterns

### Class activation check

```python
row = df[df['name'] == 'OPERCMDS']
if row.empty or row['CLASSACT'].values[0] != 'YES':
    status = 'FAIL'
    detail = "OPERCMDS class is not active"
    findings = [{'name': 'OPERCMDS', 'CLASSACT': 'NO'}]
else:
    status = 'PASS'
    detail = "OPERCMDS class is active"
```

### STARTED profile check

```python
started = df[df['GRST_CLASS_NAME'] == 'STARTED']
profiles = started[started['GRST_NAME'].str.upper().str.startswith('SDSF')]
if profiles.empty:
    status = 'FAIL'
    detail = "No STARTED class profile for SDSF"
    findings = [{'GRST_CLASS_NAME': 'STARTED', 'GRST_NAME': 'SDSF.*', 'GRST_USER_ID': 'MISSING'}]
else:
    status = 'PASS'
    detail = f"Found {len(profiles)} STARTED profile(s) for SDSF"
    findings = profiles.to_dict('records')
```

### STC userid PROTECTED check

```python
row = df[df['USBD_NAME'].str.upper() == 'SDSF']
if row.empty:
    status = 'FAIL'
    detail = "STC userid SDSF not found in RACF database"
    findings = [{'USBD_NAME': 'SDSF', 'USBD_NOPWD': 'NOT DEFINED'}]
else:
    nopwd = row['USBD_NOPWD'].values[0]
    if nopwd == 'YES':
        status = 'PASS'
        detail = "SDSF userid is PROTECTED (NOPASSWORD)"
    else:
        status = 'FAIL'
        detail = f"SDSF userid is not PROTECTED — NOPASSWORD={nopwd}"
    findings = row[['USBD_NAME', 'USBD_NOPWD']].to_dict('records')
```

### Deny-by-default profile check

```python
cls_df = df[df['GRBD_CLASS_NAME'] == 'MQCONN']
deny_all = cls_df[cls_df['GRBD_NAME'] == '**']
if deny_all.empty:
    status = 'FAIL'
    detail = "No deny-by-default profile ** in MQCONN"
    findings = [{'GRBD_CLASS_NAME': 'MQCONN', 'GRBD_NAME': '**', 'GRBD_UACC': 'MISSING'}]
else:
    uacc = deny_all['GRBD_UACC'].values[0]
    status = 'PASS' if str(uacc).upper() == 'NONE' else 'FAIL'
    detail = f"MQCONN ** profile UACC={uacc}"
    findings = deny_all.to_dict('records')
```

### Cross-DataFrame check

```python
# Find STARTED profiles that assign non-PROTECTED userids
started = df[df['GRST_CLASS_NAME'] == 'STARTED']
bad = []
for _, row in started.iterrows():
    uid = row['GRST_USER_ID']
    user_rows = users_df[users_df['USBD_NAME'] == uid]
    if user_rows.empty or user_rows['USBD_NOPWD'].values[0] != 'YES':
        entry = row.to_dict()
        entry['ISSUE'] = 'NOT PROTECTED'
        bad.append(entry)
if bad:
    status = 'FAIL'
    detail = f"{len(bad)} STARTED profile(s) assign non-PROTECTED userid"
    findings = bad
else:
    status = 'PASS'
    detail = "All STARTED profiles assign PROTECTED userids"
```

### REVIEW verdict

Use `'REVIEW'` when the data is present but a human must validate it:

```python
trusted = df[
    (df['GRST_CLASS_NAME'] == 'STARTED') &
    (df['GRST_TRUSTED'] == 'YES')
]
if trusted.empty:
    status = 'PASS'
    detail = "No TRUSTED profiles found in STARTED class"
else:
    status = 'REVIEW'
    detail = f"{len(trusted)} STARTED profile(s) with TRUSTED attribute — verify each is justified"
    findings = trusted.to_dict('records')
```

### SKIP verdict

Use `'SKIP'` when a required prerequisite is absent:

```python
if dcollect is None:
    status = 'SKIP'
    detail = "DCOLLECT data not provided (pass --dcollect)"
else:
    ds = dcollect.datasets
    # ... rest of the check
```

---

## Tips

- DataFrames from IRRDBU00 may use `NaN` for absent fields. Coerce with `str(value)` or `.fillna('')` before string comparisons.
- String comparisons in RACF data are case-sensitive. Use `.str.upper()` when the input casing is unknown.
- `to_dict('records')` converts a filtered DataFrame to a list of dicts suitable for `findings`.
- Avoid modifying `df` in-place; use a copy (`df.copy()`) or assign to a new variable.
- The `logic` block runs in a controlled `exec()` with a fresh local namespace. Do not rely on module-level globals beyond the injected variables.

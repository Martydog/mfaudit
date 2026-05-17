# Hard examples — `python` engine

Use the `python` engine when the check cannot be expressed as a single filter:

- The verdict depends on data from **more than one DataFrame**
- You need **conditional branching** (if X then check Y, else check Z)
- Some findings require a **human review** rather than an automatic PASS/FAIL
- A data source might not be present and the control should **SKIP** gracefully

---

## How the `python` engine works

Your YAML has a `logic:` key containing a block of Python source code. The engine runs that code in a controlled environment with a set of pre-loaded variables (DataFrames, the full IRRDBU00/SETROPTS objects, and the pandas module). When the code finishes, the engine reads three output variables you must set:

| Variable | Required | What it does |
|---|---|---|
| `status` | **Yes** | The verdict: `'PASS'`, `'FAIL'`, `'REVIEW'`, or `'SKIP'` |
| `detail` | No | A one-line summary shown under the verdict in the report |
| `findings` | No | A list of dicts — each dict becomes a row in the findings table |

If `logic` exits without setting `status`, the control is marked **ERROR** and the traceback appears on the console.

The `assertion:` block with `type: python_result` is **documentation-only**. The engine ignores it at runtime. It exists so someone reading the YAML can understand the intent without running the code. Always include it — it makes the YAML self-describing.

```yaml
assertion:
  type: python_result
  pass_message: "What PASS means in plain English"
  fail_message: "What FAIL means in plain English"
```

---

## Example 1 — All STARTED profiles must assign PROTECTED userids

**What it checks:** Every profile in the RACF `STARTED` class assigns a userid to a started task. If that userid is not defined with `NOPASSWORD` (the PROTECTED flag), it could theoretically be logged into interactively — a serious security gap.

This check requires two DataFrames: `irrdbu00.generalSTDATA` (the STARTED profiles) and `irrdbu00.users` (to look up the NOPASSWORD flag for each assigned userid). That cross-DataFrame join is why `pandas_query` cannot do it.

```yaml
controls:
  - control_id: CUSTOM-STC-PROTECTED
    title: "All STARTED class profiles must assign PROTECTED userids"
    severity: high
    custom:
      benchmark: "Internal policy"
      category:  "Started tasks"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: python
      dataset: "irrdbu00.generalSTDATA + irrdbu00.users"    # (1)
      select_columns:
        - GRST_CLASS_NAME
        - GRST_NAME
        - GRST_USER_ID
      assertion:                                             # (2)
        type: python_result
        pass_message: "All STARTED profiles assign PROTECTED userids"
        fail_message:  "One or more STARTED profiles assign non-PROTECTED userids"
      logic: |
        # (3) Narrow to STARTED class profiles only
        started = df[df['GRST_CLASS_NAME'] == 'STARTED']    # (4)

        bad = []
        for _, row in started.iterrows():                    # (5)
            uid = row['GRST_USER_ID']

            # (6) Skip special values that are not real userids
            if str(uid).strip().upper() in ('', 'NAN', '**MEMBER**'):
                continue

            # (7) Look up the userid in the users DataFrame
            user_row = users_df[users_df['USBD_NAME'] == uid]

            if user_row.empty:
                # Userid referenced in STARTED profile does not exist in RACF
                bad.append({
                    'GRST_NAME':    row['GRST_NAME'],
                    'GRST_USER_ID': uid,
                    'ISSUE':        'Userid not defined in RACF',
                })
            elif user_row['USBD_NOPWD'].values[0] != 'YES':   # (8)
                bad.append({
                    'GRST_NAME':    row['GRST_NAME'],
                    'GRST_USER_ID': uid,
                    'ISSUE':        'Not PROTECTED (NOPASSWORD not set)',
                })

        if bad:
            status  = 'FAIL'
            detail  = f"{len(bad)} STARTED profile(s) assign non-PROTECTED userid(s)"
            findings = bad                                     # (9)
        else:
            status = 'PASS'
            detail = "All STARTED profiles assign PROTECTED userids"
    remediation: >
      For each listed userid, issue:
        ALTUSER <userid> NOPASSWORD
      If the userid does not exist, define it and assign it NOPASSWORD:
        ADDUSER <userid> NOPASSWORD
      Then verify the STARTED profile still points to the correct userid.
```

### Line-by-line explanation

**(1) `dataset: "irrdbu00.generalSTDATA + irrdbu00.users"`**
The `+` syntax tells the engine to load two DataFrames. Each component gets a fixed variable name in `logic`:

- `irrdbu00.generalSTDATA` → `df` (because it's not one of the named shortcuts)
- `irrdbu00.users` → `users_df`

See the [combined dataset reference](../authoring/schema.md#combined-dataset-specs) for the full variable-name table.

**(2) `assertion: type: python_result`**
Pure documentation. The engine reads `status` from your `logic` block — these messages are never executed. Write them so a colleague can understand the control without reading the Python.

**(3) Narrowing to STARTED profiles**
`irrdbu00.generalSTDATA` contains STDATA segments for ALL general resource classes, not just STARTED. Always filter to the class you care about before iterating.

**(4) `df[df['GRST_CLASS_NAME'] == 'STARTED']`**
Standard pandas boolean indexing. The result is a new DataFrame containing only rows where the class name is `'STARTED'`. The original `df` is not modified.

**(5) `for _, row in started.iterrows()`**
Iterates row by row. The `_` discards the integer index (we don't need it). `row` is a pandas `Series` — access columns with `row['COLUMN_NAME']`.

!!! tip "When to iterate vs. vectorise"
    For a check like this — where you need to look up each row's value in a second DataFrame — row-by-row iteration is the clearest approach. Vectorised merges are faster but harder to read and debug. For audit controls, clarity beats speed.

**(6) Skipping non-userid values**
STARTED profiles can have special userid values that are not real RACF userids (e.g. blank, `**MEMBER**`). Always guard against these to avoid false positives. `str(uid).strip().upper()` normalises the value before comparison; the `.upper()` is defensive since casing should be consistent but may vary in edge cases.

**(7) `users_df[users_df['USBD_NAME'] == uid]`**
Looks up the userid in the users DataFrame. The result is a (possibly empty) DataFrame. We check `.empty` before accessing `.values[0]` to avoid an IndexError.

**(8) `user_row['USBD_NOPWD'].values[0]`**
`.values` extracts the underlying NumPy array; `[0]` takes the first element. This is the standard idiom for reading a single value from a one-row DataFrame. The column `USBD_NOPWD` is `'YES'` when the userid has `NOPASSWORD` set (i.e. is PROTECTED).

**(9) `findings = bad`**
`findings` must be a list of dicts. Each dict becomes one row in the report's findings table. The keys become column headers. Build a custom dict (as we do here) rather than dumping the whole row with `row.to_dict()` when you want clean, readable column names or want to add an `ISSUE` column.

---

## Example 2 — No UID=0 user unless they are PROTECTED

**What it checks:** Unix System Services (USS) UID 0 is the superuser equivalent on z/OS. Any RACF userid with UID 0 must also have `NOPASSWORD` set — otherwise it could be used to log in interactively as root.

```yaml
  - control_id: CUSTOM-UID0-PROTECTED
    title: "All UID=0 accounts must be PROTECTED (NOPASSWORD)"
    severity: high
    custom:
      benchmark: "Internal policy"
      category:  "Unix System Services"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: python
      dataset: "irrdbu00.userOMVS + irrdbu00.users"
      select_columns: [USOMVS_NAME, USOMVS_UID, USBD_NOPWD]
      assertion:
        type: python_result
        pass_message: "All UID=0 accounts are PROTECTED"
        fail_message:  "One or more UID=0 accounts are not PROTECTED"
      logic: |
        # (1) All userids that have a USS OMVS segment with UID=0
        uid0 = omvs_df[omvs_df['USOMVS_UID'] == 0]     # (2)

        if uid0.empty:
            status = 'PASS'
            detail = "No UID=0 accounts defined"
        else:
            bad = []
            for _, row in uid0.iterrows():
                name = row['USOMVS_NAME']
                user = users_df[users_df['USBD_NAME'] == name]
                if user.empty:
                    bad.append({
                        'USOMVS_NAME': name,
                        'USOMVS_UID':  0,
                        'ISSUE':       'Base userid not found in RACF',
                    })
                elif user['USBD_NOPWD'].values[0] != 'YES':
                    bad.append({
                        'USOMVS_NAME': name,
                        'USOMVS_UID':  0,
                        'USBD_NOPWD':  user['USBD_NOPWD'].values[0],
                        'ISSUE':       'Not PROTECTED',
                    })

            if bad:
                status   = 'FAIL'
                detail   = f"{len(bad)} UID=0 account(s) are not PROTECTED"
                findings = bad
            else:
                status = 'PASS'
                detail = f"All {len(uid0)} UID=0 account(s) are PROTECTED"
    remediation: >
      For each listed userid:
        ALTUSER <userid> NOPASSWORD
```

### Key points

**(1) `dataset: "irrdbu00.userOMVS + irrdbu00.users"`**
`irrdbu00.userOMVS` → `omvs_df`; `irrdbu00.users` → `users_df`. The naming convention is described in the [python engine docs](../authoring/python-engine.md#multi-dataframe-dataset-specs).

**(2) `omvs_df[omvs_df['USOMVS_UID'] == 0]`**
`USOMVS_UID` is an integer column in mfpandas, so we compare with `0` not `'0'`. If you are unsure of a column's type, check with `print(df.dtypes)` in a test script before writing the control.

Notice the **early exit**: if there are no UID=0 accounts at all, we return PASS immediately and skip the loop entirely. This is good practice — don't iterate over an empty DataFrame.

---

## Example 3 — Critical classes must be both ACTIVE and RACLIST'd (with REVIEW)

**What it checks:** Certain RACF resource classes must be not just activated (`CLASSACT`) but also memory-resident (`RACLIST`) for performance and security reasons. A class that is active but not RACLIST'd still works, but is a configuration gap worth flagging for review.

This example introduces the **`REVIEW`** verdict: something that is not automatically a failure but that a human must inspect.

```yaml
  - control_id: CUSTOM-CRITICAL-CLASSES
    title: "Critical RACF classes must be ACTIVE and RACLIST'd"
    severity: medium
    custom:
      benchmark: "Internal policy"
      category:  "Class activation"
    data_sources_needed: [setropts]
    implementation:
      engine: python
      dataset: setropts.classInfo
      select_columns: [name, CLASSACT, RACLIST]
      assertion:
        type: python_result
        pass_message:  "All critical classes are ACTIVE and RACLIST'd"
        fail_message:  "One or more critical classes are not ACTIVE"
      logic: |
        # (1) The set of classes your site considers critical
        REQUIRED_CLASSES = [
            'FACILITY', 'OPERCMDS', 'TSOAUTH',
            'STARTED',  'DATASET',  'UNIXPRIV',
        ]

        fail_list   = []   # class is not active at all → definite FAIL
        review_list = []   # class is active but not RACLIST'd → needs review

        for cls in REQUIRED_CLASSES:
            row = df[df['name'] == cls]            # (2)

            if row.empty:
                fail_list.append({'name': cls, 'CLASSACT': 'NOT FOUND', 'RACLIST': 'NOT FOUND'})
                continue

            classact = row['CLASSACT'].values[0]
            raclist  = row['RACLIST'].values[0]

            if classact != 'YES':
                fail_list.append({'name': cls, 'CLASSACT': classact, 'RACLIST': raclist})
            elif raclist != 'YES':                 # (3)
                review_list.append({'name': cls, 'CLASSACT': classact, 'RACLIST': raclist})

        # (4) Decide the overall verdict
        if fail_list:
            status   = 'FAIL'
            detail   = f"{len(fail_list)} critical class(es) not active"
            findings = fail_list + review_list
        elif review_list:
            status   = 'REVIEW'                   # (5)
            detail   = f"{len(review_list)} class(es) active but not RACLIST'd — verify"
            findings = review_list
        else:
            status = 'PASS'
            detail = "All critical classes are ACTIVE and RACLIST'd"
    remediation: >
      To activate a class and make it memory-resident:
        SETROPTS CLASSACT(<class>) RACLIST(<class>)
      After activating, always refresh:
        SETROPTS RACLIST(<class>) REFRESH
```

### Key points

**(1) Defining your own constants**
The `logic` block is ordinary Python. You can define constants, helper variables, loops — anything you need. The only constraint is that you must not `import` modules (only the injected variables are available). Constants defined at the top of the block make the logic easy to update without touching the control structure.

**(2) `df[df['name'] == cls]`**
`setropts.classInfo` has a column called `name` (lowercase). RACF class names are stored in uppercase. The comparison is exact — `'facility'` would not match.

**(3) Two-tier severity**
Not active at all → definite `FAIL`. Active but not RACLIST'd → ambiguous — some sites deliberately choose not to RACLIST every class. We separate these into two lists and combine them into `findings` only if there are failures.

**(4) Verdict priority**
If _any_ class is outright inactive, the whole control is `FAIL`. Only if everything is active but some classes are not RACLIST'd do we downgrade to `REVIEW`. This ordering ensures the most severe condition always wins.

**(5) `status = 'REVIEW'`**
Use `REVIEW` when the data is present but a human must make a judgement call. The report renders `REVIEW` differently from `FAIL` — it appears with a distinct colour and label so reviewers know it requires investigation, not just remediation.

---

## Example 4 — DCOLLECT check with graceful SKIP

**What it checks:** Production datasets (those matching the `PROD.**` HLQ) should all have an SMS Management Class assigned. Datasets without one are not subject to automatic backup and expiry policies.

This check uses DCOLLECT data, which is optional. If `--dcollect` was not passed to `mfaudit`, the control must SKIP cleanly rather than crash.

```yaml
  - control_id: CUSTOM-PROD-SMS-MGMT
    title: "All PROD.** datasets must have an SMS Management Class"
    severity: medium
    custom:
      benchmark: "Internal policy"
      category:  "Storage management"
    data_sources_needed: [dcollect]          # (1)
    implementation:
      engine: python
      dataset: dcollect.datasets             # (2)
      select_columns: [NAME, TYPE, MGMTCLAS]
      assertion:
        type: python_result
        pass_message: "All PROD.** datasets have an SMS Management Class"
        fail_message:  "One or more PROD.** datasets have no SMS Management Class"
      logic: |
        # (1) Always check for None before using dcollect
        if dcollect is None:                  # (3)
            status = 'SKIP'
            detail = "DCOLLECT data not provided — pass --dcollect to enable this check"
        else:
            ds = dcollect.datasets

            # (4) Filter to PROD.** datasets
            prod = ds[ds['NAME'].str.upper().str.startswith('PROD.')]

            if prod.empty:
                status = 'SKIP'
                detail = "No datasets matching PROD.** found in DCOLLECT"
            else:
                # (5) Missing Management Class appears as NaN or blank
                no_mgmt = prod[
                    prod['MGMTCLAS'].isna() |
                    (prod['MGMTCLAS'].str.strip() == '')
                ]

                if no_mgmt.empty:
                    status = 'PASS'
                    detail = f"All {len(prod)} PROD.** dataset(s) have an SMS Management Class"
                else:
                    status   = 'FAIL'
                    detail   = f"{len(no_mgmt)} PROD.** dataset(s) have no SMS Management Class"
                    findings = no_mgmt[['NAME', 'TYPE', 'MGMTCLAS']].to_dict('records')   # (6)
    remediation: >
      Assign an SMS Management Class to each listed dataset:
        ALTER '<dataset>' MGMTCLAS(<class>)
      Contact your SMS administrator to determine the correct Management Class
      for each dataset type.
```

### Line-by-line explanation

**(1) `data_sources_needed: [dcollect]`**
Declaring `dcollect` here tells the runner that this control needs DCOLLECT data. If `--dcollect` is not passed, the runner will set the control to SKIP automatically — but we also guard in `logic` (see below) for safety.

**(2) `dataset: dcollect.datasets`**
When `--dcollect` is not provided, `dcollect` is `None`. The engine still sets `df = None` in this case — which is why we must check before using it.

**(3) `if dcollect is None: status = 'SKIP'`**
This is the canonical SKIP guard. Always check `dcollect is None` at the top of any DCOLLECT-dependent `logic` block. It allows the control to be included in a shared controls file even on systems where DCOLLECT output is not available — it simply shows as SKIP in the report rather than ERROR.

**(4) `ds['NAME'].str.upper().str.startswith('PROD.')`**
Dataset names in DCOLLECT are typically uppercase already, but `.str.upper()` is a defensive habit — it costs nothing and prevents false negatives from inconsistent casing. `.str.startswith()` matches any name beginning with `PROD.`, which covers all levels of the hierarchy.

**(5) Checking for missing SMS class**
DCOLLECT stores absent SMS attributes as `NaN` (pandas null). A dataset may also have a blank string if the field was exported but empty. The two-part condition `.isna() | (... == '')` handles both cases. Always use this pattern when checking optional string fields from DCOLLECT.

**(6) `no_mgmt[['NAME', 'TYPE', 'MGMTCLAS']].to_dict('records')`**
`.to_dict('records')` converts a DataFrame to a list of dicts — one dict per row. Selecting only the columns you need with `[['NAME', 'TYPE', 'MGMTCLAS']]` keeps the findings table clean. The alternative — `no_mgmt.to_dict('records')` — dumps every column, which can be overwhelming for wide DataFrames.

---

## Summary — choosing your verdict

| Situation | Verdict |
|---|---|
| Check passed, nothing to act on | `'PASS'` |
| Policy violated, clear remediation exists | `'FAIL'` |
| Data present but human judgement required | `'REVIEW'` |
| Required data source not available | `'SKIP'` |

Avoid using `'REVIEW'` as a fallback for checks that are actually well-defined. Reserve it for genuinely ambiguous situations — like TRUSTED profiles in STARTED — where the presence of the condition does not automatically mean a violation.

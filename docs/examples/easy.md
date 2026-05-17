# Easy examples — `pandas_query` engine

The `pandas_query` engine is the right choice whenever the entire check boils down to: _"run a filter on one DataFrame; if any rows survive, that's a failure."_

You write a `filter` expression (standard pandas `.query()` syntax) and pick an `assertion` type. No Python required.

---

## Example 1 — No active user holds both SPECIAL and OPERATIONS

**What it checks:** A user with both `SPECIAL` and `OPERATIONS` attributes effectively owns the entire system. This combination should never appear on a non-revoked account.

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
      engine: pandas_query
      dataset: irrdbu00.users          # (1)
      select_columns:                  # (2)
        - USBD_NAME
        - USBD_SPECIAL
        - USBD_OPER
        - USBD_REVOKE
      filter: >                        # (3)
        USBD_SPECIAL == 'YES' and
        USBD_OPER    == 'YES' and
        USBD_REVOKE  != 'YES'
      assertion:                       # (4)
        type: no_rows
        pass_message: "No active user holds both SPECIAL and OPERATIONS"
        fail_message: "{n} user(s) hold both SPECIAL and OPERATIONS"
    remediation: >
      Remove one of the attributes from each listed userid:
        ALTUSER <userid> NOSPECIAL
      or
        ALTUSER <userid> NOOPER
```

### Line-by-line explanation

**(1) `dataset: irrdbu00.users`**
This tells the engine which DataFrame to load. `irrdbu00.users` contains one row per RACF user, sourced from the type-0200 records in the IRRDBU00 unload. See the [dataset reference](../authoring/schema.md#dataset-dotted-path-reference) for the full list.

**(2) `select_columns`**
These columns are shown in the findings table in the report. They have no effect on the filter logic — they're purely for readability. Include enough columns that a reviewer can identify and act on each finding without opening a separate tool. Here we include `USBD_REVOKE` so a reviewer can verify the filter is working correctly.

**(3) `filter`**
A pandas `.query()` expression string. String literals must use single quotes. Multiple conditions can be combined with `and` / `or`. The YAML `>` block scalar collapses the three lines into a single string — this is just a readability choice; you could also write it on one line.

The filter is applied with `df.query(filter_string)`. Every row that _survives_ the filter is a finding. The assertion then decides what surviving rows mean.

!!! tip "String values in RACF DataFrames"
    IRRDBU00 fields that hold YES/NO flags (like `USBD_SPECIAL`) always contain the literal strings `'YES'` or `'NO'` — never Python booleans. Always compare with quoted strings.

**(4) `assertion: type: no_rows`**
The simplest assertion: PASS when the filtered DataFrame is empty; FAIL when it contains at least one row. Each surviving row becomes a row in the report's findings table.

`{n}` in `fail_message` is replaced at runtime with the actual row count. `pass_message` and `fail_message` are both optional — if you omit them, sensible defaults are used. Write them anyway: they appear in the report and make findings easier to understand at a glance.

---

## Example 2 — PASSWORD HISTORY must be at least 4

**What it checks:** RACF's `PASSWORD(HISTORY)` setting controls how many previous passwords are remembered to prevent reuse. The CIS z/OS Benchmark requires a minimum of 4.

```yaml
  - control_id: CIS-1.1.2
    title: "Ensure PASSWORD(HISTORY) is set to at least 4"
    severity: medium
    cis:
      section: "1.1.2"
      level: L1
      benchmark: "CIS z/OS RACF Benchmark"
    data_sources_needed: [setropts]
    implementation:
      engine: pandas_query
      dataset: setropts.fieldInfo        # (1)
      select_columns: [Setting, Value]
      filter: "Setting == 'HISTORY'"     # (2)
      assertion:
        type: scalar_compare             # (3)
        operator: ">="
        expected: 4
        pass_message: "PASSWORD HISTORY is {value} (≥ 4)"
        fail_message: "PASSWORD HISTORY is only {value} — must be ≥ 4"
    remediation: >
      Increase the password history retention:
        SETROPTS PASSWORD(HISTORY(4))
```

### Line-by-line explanation

**(1) `dataset: setropts.fieldInfo`**
`setropts.fieldInfo` is a two-column DataFrame: `Setting` and `Value`. Each SETROPTS password/passphrase/audit flag is one row. This is the right place to look for numeric policy thresholds like HISTORY, INTERVAL, MINLENGTH, etc.

**(2) `filter: "Setting == 'HISTORY'"`**
This narrows the DataFrame to the single row for the HISTORY setting. The `scalar_compare` assertion then reads the `Value` column from that row.

**(3) `assertion: type: scalar_compare`**
Reads the `Value` column from the first surviving row, coerces it to an integer if possible, then applies `operator` against `expected`. Here, `>=` means _"the actual value must be greater than or equal to 4"_.

Supported operators: `<=`, `>=`, `<`, `>`, `==`, `!=`

`{value}` in both messages is replaced with the actual value read from the DataFrame. This lets reviewers see the current configuration at a glance in the report without having to go back to the raw data.

!!! warning "What if the setting is missing?"
    If the `filter` returns zero rows (the setting is not present in the SETROPTS export), `scalar_compare` returns **FAIL** with the detail `"Setting not found in data"`. This is intentional: a missing setting means RACF is using a default, which may or may not be compliant. Treat it as a failure and verify manually.

---

## Example 3 — No dataset profile has UACC=ALTER

**What it checks:** A dataset profile with Universal Access (`UACC`) set to `ALTER` grants every user on the system full read/write/delete rights. This should never appear in a production RACF database.

```yaml
  - control_id: CUSTOM-NO-UACC-ALTER
    title: "No dataset profile may have UACC=ALTER"
    severity: high
    custom:
      benchmark: "Internal policy"
      category:  "Dataset protection"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: pandas_query
      dataset: irrdbu00.datasets         # (1)
      select_columns: [DSBD_NAME, DSBD_UACC, DSBD_OWNER_ID]
      filter: "DSBD_UACC == 'ALTER'"     # (2)
      assertion:
        type: no_rows
        pass_message: "No dataset profiles with UACC=ALTER"
        fail_message: "{n} dataset profile(s) found with UACC=ALTER"
    remediation: >
      Reduce the UACC for each listed profile to the minimum required:
        ALTDSD '<profile>' UACC(READ)
      or
        ALTDSD '<profile>' UACC(NONE)
      Then review the access list to grant explicit access where needed.
```

### Line-by-line explanation

**(1) `dataset: irrdbu00.datasets`**
Dataset profiles live in `irrdbu00.datasets` (type-0400 records). Each row is one profile. The key columns are `DSBD_NAME` (profile name), `DSBD_UACC` (universal access level), and `DSBD_OWNER_ID` (owner).

**(2) `filter: "DSBD_UACC == 'ALTER'"`**
UACC values in IRRDBU00 are stored as uppercase strings: `'NONE'`, `'EXECUTE'`, `'READ'`, `'UPDATE'`, `'ALTER'`, `'CONTROL'`. The comparison is case-sensitive, but because RACF itself stores them uppercase you don't need `.str.upper()` here.

We include `DSBD_OWNER_ID` in `select_columns` so the findings table shows who owns the offending profile — useful when triaging which team to contact.

---

## Putting it all together — a complete file

Here is a minimal but complete `example_controls.yaml` file you can save alongside your other YAML files and pass to `mfaudit` with `--controls`:

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
      engine: pandas_query
      dataset: irrdbu00.users
      select_columns: [USBD_NAME, USBD_SPECIAL, USBD_OPER]
      filter: "USBD_SPECIAL == 'YES' and USBD_OPER == 'YES' and USBD_REVOKE != 'YES'"
      assertion:
        type: no_rows
        fail_message: "{n} active user(s) hold both SPECIAL and OPERATIONS"
    remediation: "ALTUSER <userid> NOSPECIAL  or  ALTUSER <userid> NOOPER"

  - control_id: CUSTOM-NO-UACC-ALTER
    title: "No dataset profile may have UACC=ALTER"
    severity: high
    custom:
      benchmark: "Internal policy"
      category:  "Dataset protection"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: pandas_query
      dataset: irrdbu00.datasets
      select_columns: [DSBD_NAME, DSBD_UACC]
      filter: "DSBD_UACC == 'ALTER'"
      assertion:
        type: no_rows
        fail_message: "{n} dataset profile(s) with UACC=ALTER"
    remediation: "ALTDSD '<profile>' UACC(READ)"
```

Run it:

```bash
mfaudit --irrdbu00 /path/to/IRRDBU00 \
        --setropts  /path/to/SETROPTS \
        --controls  example_controls.yaml \
        --out       out/
```

---

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Comparing `USBD_SPECIAL == True` | Never matches — RACF stores `'YES'` not `True` | Use `== 'YES'` |
| Forgetting `USBD_REVOKE != 'YES'` in a privilege check | Revoked accounts appear as violations | Add the revoke exclusion to your filter |
| `filter` uses double quotes inside a double-quoted YAML string | YAML parse error | Use single quotes for string literals inside `filter` |
| `scalar_compare` on a setting that might not exist | Returns FAIL with "Setting not found" — may be unexpected | Acceptable; document in `fail_message` |

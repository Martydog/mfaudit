# Custom controls

Any rule that does not map to a published CIS control can be added as a custom control. The engine and YAML schema are identical — the only difference is the `custom:` citation block instead of `cis:`.

---

## Minimal example

```yaml
controls:
  - control_id: CUSTOM-NODUAL-PRIVS
    title: "No active user may hold both SPECIAL and OPERATIONS simultaneously"
    severity: high
    custom:
      benchmark: "Internal policy"
      category:  "Privileged access"
      reference: "Security Standard SEC-4.2"
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
        if hits.empty:
            status = 'PASS'
            detail = "No active user holds both SPECIAL and OPERATIONS"
        else:
            status = 'FAIL'
            detail = f"{len(hits)} user(s) hold both SPECIAL and OPERATIONS"
            findings = hits[['USBD_NAME', 'USBD_SPECIAL', 'USBD_OPER']].to_dict('records')
    remediation: >
      For each identified userid, remove either SPECIAL or OPERATIONS using:
      ALTUSER <userid> NOSPECIAL  or  ALTUSER <userid> NOOPER
```

---

## `custom:` citation block

```yaml
custom:
  benchmark: "Internal policy"   # or a regulation name, e.g. "PCI-DSS v4.0"
  category:  "Privileged access" # section label shown in the report
  reference: "SEC-4.2"           # your internal policy reference (optional)
```

The `custom:` block replaces the `cis:` block. All other fields are identical.

---

## pandas_query example

When the test is a single filter, `pandas_query` is simpler:

```yaml
  - control_id: CUSTOM-REVOKED-SPECIALS
    title: "Ensure no revoked users hold SPECIAL attribute"
    severity: medium
    custom:
      benchmark: "Internal cleanup"
      category: "User management"
    data_sources_needed: [irrdbu00]
    implementation:
      engine: pandas_query
      dataset: irrdbu00.users
      select_columns: [USBD_NAME, USBD_SPECIAL, USBD_REVOKE]
      filter: "USBD_SPECIAL == 'YES' and USBD_REVOKE == 'YES'"
      assertion:
        type: no_rows
        pass_message: "No revoked users hold SPECIAL attribute"
        fail_message: "Revoked user(s) still hold SPECIAL attribute"
    remediation: >
      Remove SPECIAL from revoked accounts: ALTUSER <userid> NOSPECIAL
```

---

## Naming conventions

- Prefix: `CUSTOM-` followed by a short descriptive slug, e.g. `CUSTOM-NO-DUAL-PRIVS`
- IDs must be unique across all loaded control files
- Keep IDs stable — they appear in the CSV and report; changing them breaks trend comparisons

---

## Storing custom controls

Put custom controls in a separate file (e.g. `example_controls.yaml`) and pass it alongside the standard libraries:

```bash
mfaudit --controls controls.yaml example_controls.yaml --out out/
```

---

## Real-world example — `example_controls.yaml`

The repository ships with `example_controls.yaml` containing a ready-to-run shop-floor control. It demonstrates several advanced patterns: cross-DataFrame access analysis, prefix-based filtering, vectorised group-membership joins, sorted findings with a `VIA_GROUP` column, and a split direct/indirect detail count.

**What it checks:** Batch service accounts (user IDs starting with `B`) must never gain access to customer data profiles (dataset profiles starting with `C`) — either directly (B-user on the access list itself) or indirectly (a group is on the access list and that group contains B-prefixed members). Any such access is a policy violation that needs a business justification.

```yaml
controls:
  - control_id: CUSTOM-AC-1
    title: "B-prefixed users must not access C-prefixed dataset profiles (direct or via group)"
    severity: high
    custom:
      benchmark: "Internal Access Control Policy"
      category:  "Access Control"
      reference: "IAC-DS-001"                      # (1)
    data_sources_needed: [irrdbu00]
    implementation:
      engine: python
      dataset: irrdbu00.datasetAccess              # (2)
      select_columns: [DSACC_NAME, DSACC_AUTH_ID, DSACC_ACCESS, VIA_GROUP]
      assertion:
        type: python_result
        pass_message: "No B-prefixed users access C-prefixed dataset profiles (direct or via group)"
        fail_message:  "B-user(s) found with access to C-dataset profile(s)"
      logic: |
        # All access list entries for C-prefixed dataset profiles
        c_access = df[df['DSACC_NAME'].str.upper().str.startswith('C')].copy()  # (3)

        # --- Direct hits: B-prefixed user IDs on the access list ---
        direct = c_access[
            c_access['DSACC_AUTH_ID'].str.upper().str.startswith('B')
        ][['DSACC_NAME', 'DSACC_AUTH_ID', 'DSACC_ACCESS']].copy()
        direct['VIA_GROUP'] = ''                                                 # (4)

        # --- Indirect hits: groups on the access list that contain B-prefixed members ---
        potential_groups = c_access[
            ~c_access['DSACC_AUTH_ID'].str.upper().str.startswith('B')
        ]

        connect = irrdbu00.connectData                                           # (5)
        b_members = connect[connect['USCON_NAME'].str.upper().str.startswith('B')]

        indirect = potential_groups.merge(                                       # (6)
            b_members[['USCON_GRP_ID', 'USCON_NAME']],
            left_on='DSACC_AUTH_ID',
            right_on='USCON_GRP_ID',
            how='inner'
        )
        indirect = indirect[['DSACC_NAME', 'USCON_NAME', 'DSACC_ACCESS', 'DSACC_AUTH_ID']].copy()
        indirect.columns = ['DSACC_NAME', 'DSACC_AUTH_ID', 'DSACC_ACCESS', 'VIA_GROUP']

        # Combine, sort, emit
        all_df = pd.concat([direct, indirect], ignore_index=True)               # (7)
        all_df = all_df.sort_values(['DSACC_NAME', 'VIA_GROUP', 'DSACC_AUTH_ID'])

        count        = len(all_df)
        direct_count = len(direct)
        group_count  = len(indirect)
        status  = 'PASS' if count == 0 else 'FAIL'
        detail  = (
            f"{count} B-user access(es) to C-dataset profiles "
            f"({direct_count} direct, {group_count} via group)"
        )
        findings = all_df.to_dict('records')
    remediation: >
      For each finding, remove the permit:
        PERMIT '<dataset-profile>' ID(<userid-or-group>) DELETE
      If the finding is via a group, either remove the B-user from the group
      or remove the group from the dataset profile access list.
      If access is genuinely required, raise a business justification and
      re-assign it to a non-B-prefixed identity.
```

### What each part does

**(1) `custom:` citation block with `reference`**
The `reference` field is optional but useful — it ties the control to your internal policy document. It appears in the report so auditors can trace the finding back to the requirement without leaving the report.

**(2) `dataset: irrdbu00.datasetAccess`**
`irrdbu00.datasetAccess` (type-0410 records) contains one row per access list entry — who has what level of access to which dataset profile. The key columns here are `DSACC_NAME` (profile name), `DSACC_AUTH_ID` (the user or group granted access), and `DSACC_ACCESS` (the access level: READ, UPDATE, ALTER, etc.).

The `select_columns` list includes `VIA_GROUP` even though that column does not exist in the raw DataFrame — it is added in the `logic` block. `select_columns` controls which columns appear in the report findings table, so listing it here ensures the column is visible to reviewers.

**(3) Pre-filter on `c_access`**
The very first step narrows the working set to C-prefixed dataset profiles. Every subsequent operation works on this smaller slice, which keeps the merge in step (6) fast on large RACF databases.

**(4) `VIA_GROUP` sentinel for direct hits**
Direct findings have an empty `VIA_GROUP` column (set to `''`). This keeps the schema consistent between the direct and indirect DataFrames so they can be concatenated cleanly. In the report a blank `VIA_GROUP` cell makes it immediately clear the B-user was on the access list themselves.

**(5) `irrdbu00.connectData` — group membership**
`irrdbu00.connectData` (type-0205 records) contains one row per user-group connection. The two relevant columns are `USCON_NAME` (the user ID) and `USCON_GRP_ID` (the group). Filtering this to rows where `USCON_NAME` starts with `B` gives every B-prefixed user and the groups they belong to.

The `irrdbu00` object is available directly in `python` engine logic — see the [Controls overview](index.md#python) for the full list of injected variables.

**(6) Vectorised merge instead of a loop**
`potential_groups.merge(...)` performs a pandas inner join: it keeps only those access list entries where the `DSACC_AUTH_ID` (the group on the access list) matches a group that has at least one B-prefixed member (`USCON_GRP_ID`). The result has one row per *(dataset profile, B-user, access level, group)* combination.

After the merge, the columns are renamed so the B-user's ID lands in `DSACC_AUTH_ID` and the group through which they gained access lands in `VIA_GROUP`. This makes both sets of findings follow the same column layout.

Merging vectorially is orders of magnitude faster than iterating with a Python `for` loop, which matters when the RACF database has tens of thousands of users and groups.

**(7) `pd.concat` and split counts**
`pd.concat([direct, indirect])` stacks both finding sets into one DataFrame. The `detail` string is built from three separate counts — total, direct, and via-group — so the report summary line tells reviewers at a glance how many of the violations are straightforward permits vs. group-membership paths that may require more remediation steps.

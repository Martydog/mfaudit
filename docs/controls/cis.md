# CIS Benchmark controls

46 controls drawn from:

- **CIS IBM z/OS 2.5.0 with RACF Benchmark** v1.0.0 / v1.1.0
- **CIS IBM Db2 13 for z/OS Benchmark** v1.0.0
- **CIS IBM CICS Transaction Server 6.1 Benchmark** v1.1.0

All controls are in `controls.yaml`.

---

## Password policy (section 1.1)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-1.1.1 | Ensure PASSWORD(INTERVAL) is ≤ 90 days | medium | setropts |
| CIS-1.1.2 | Ensure PASSWORD(HISTORY) is ≥ 4 | medium | setropts |
| CIS-1.1.3 | Ensure PASSWORD(RULEn) values are set | medium | setropts |
| CIS-1.1.4 | Ensure PASSWORD(MINCHANGE) is > 0 | medium | setropts |
| CIS-1.1.5 | Ensure PASSWORD(REVOKE) is specified | medium | setropts |
| CIS-1.1.6 | Ensure KDFAES algorithm is used for password encryption | **high** | setropts |
| CIS-1.1.7 | Ensure PASSWORD(WARNING) is set | low | setropts |

## User account controls (section 1.2)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-1.2.1 | Ensure inactive users are automatically revoked | medium | setropts |
| CIS-1.2.2 | Ensure STARTED class is ACTIVE and RACLISTed | medium | setropts |
| CIS-1.2.3 | Ensure PROPCNTL class is ACTIVE and RACLISTed | medium | setropts |
| CIS-1.2.5 | Ensure STARTED-TRUSTED profiles are justified | medium | irrdbu00 |
| CIS-1.2.6 | Ensure OPERCMDS class is ACTIVE and RACLISTed | medium | setropts |
| CIS-1.2.7 | Ensure CONSOLE class is ACTIVE | medium | setropts |
| CIS-1.2.8 | Ensure FACILITY class is ACTIVE and RACLISTed | **high** | setropts |

## Privileged access (section 1.3)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-1.3.1 | Ensure use of RACF SPECIAL attribute is minimized | **high** | irrdbu00 |
| CIS-1.3.4 | Ensure all STARTED profiles specify PROTECTED user IDs | **high** | irrdbu00 |

## Access controls (section 2.1)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-2.1.3 | Ensure WHEN(PROGRAM) is active | medium | setropts |
| CIS-2.1.6 | Ensure ERASE(ALL) is set for data erasure on scratch | medium | setropts |
| CIS-2.1.7 | Ensure TEMPDSN class is active | medium | setropts |

## Class controls (section 2.2)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-2.2.2 | Ensure GENERIC is enabled for all active classes | medium | setropts |
| CIS-2.2.4 | Ensure dataset PASSWORD protection is not used | medium | setropts |

## Security flags (section 2.3)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-2.3.1 | Ensure TERMINAL is set to NONE | medium | setropts |
| CIS-2.3.2 | Ensure GENCMD is enabled for all active classes | medium | setropts |
| CIS-2.3.3 | Ensure PROTECTALL is set to FAILURES | **high** | setropts |

## Privilege controls (section 2.4)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-2.4.1 | Ensure OPERATIONS attribute assignment is tightly controlled | **high** | irrdbu00 |
| CIS-2.4.4 | Ensure UID 0 is only assigned to PROTECTED STC IDs | **high** | irrdbu00 |

## Audit and logging (section 3)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-3.1 | Ensure command violations are logged (CMDVIOL) | medium | setropts |
| CIS-3.2 | Ensure activity of SPECIAL users is being logged | medium | setropts |
| CIS-3.3 | Ensure AUDIT is set for all active RACF classes | **high** | setropts |
| CIS-3.4 | Ensure activities of OPERATIONS users are logged | **high** | setropts |
| CIS-3.5 | Ensure logon statistics are recorded | medium | setropts |
| CIS-3.6 | Ensure AUDITOR/ROAUDIT privilege is limited | medium | irrdbu00 |

## Miscellaneous (section 5)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-5.3 | Ensure ADSP is set to NOADSP | **high** | setropts |

## Cryptographic services (section 7.3)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-7.3.1 | Ensure CSFSERV class is active | medium | setropts |
| CIS-7.3.2 | Ensure CSFKEYS class is active | medium | setropts |

## JES controls (section 8)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-8.2.1 | Ensure JESSPOOL class is active | **high** | setropts |
| CIS-8.4.3 | Ensure JES(BATCHALLRACF) is set | **high** | setropts |
| CIS-8.4.4 | Ensure JES(XBMALLRACF) is set | **high** | setropts |

## Unix System Services (section 9)

| ID | Title | Severity | Data source |
|---|---|---|---|
| CIS-9.1 | Ensure SURROGAT class is ACTIVE and RACLISTed | **high** | setropts |
| CIS-9.2 | Ensure UNIXPRIV class is ACTIVE and RACLISTed | **high** | setropts |
| CIS-9.5 | Ensure newly assigned UIDs and GIDs are unique | medium | irrdbu00 |
| CIS-9.21 | Ensure BPX.SUPERUSER access is restricted | **high** | irrdbu00 |

## Db2 controls

| ID | Title | Severity | Data source |
|---|---|---|---|
| DB2-1.2.1 | Ensure DSNR class is ACTIVE and RACLISTed | **high** | setropts |
| DB2-2.1.5 | Ensure SERVAUTH class is ACTIVE and RACLISTed | **high** | setropts |

## CICS controls

| ID | Title | Severity | Data source |
|---|---|---|---|
| CICS-1.2.1 | Ensure TCICSTRN class is ACTIVE and RACLISTed | **high** | setropts |
| CICS-1.2.2 | Ensure GCICSTRN class is ACTIVE | medium | setropts |

## Shop-specific example

| ID | Title | Severity | Data source |
|---|---|---|---|
| CUSTOM-1.1 | No active user may hold both SPECIAL and OPERATIONS simultaneously | **high** | irrdbu00 |

See [Custom controls](custom.md) to add your own.

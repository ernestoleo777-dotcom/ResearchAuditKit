Synthetic replay: baseline matches, then controlled file change.

## ResearchAuditKit evidence report

Mechanical gate: **PASS**
Evidence status: **UNRESOLVED**

### File observations

| File | Status |
| --- | --- |
| results.csv | MECHANICALLY&#95;VERIFIED |

Impact analysis: **COMPLETE**

### Claims to review


Review file availability, byte changes and declared versions before updating a baseline.
Omitted or unreached claims are not certified unaffected.

### Findings

No blocking findings; accepted unresolved declarations remain unchanged.

**Boundary:** current-byte observations and user-declared relationships only. No scientific adjudication; observations are not an atomic multi-file snapshot.

## ResearchAuditKit evidence report

Mechanical gate: **FAIL**
Evidence status: **INVALID**

### File observations

| File | Status |
| --- | --- |
| results.csv | IDENTITY&#95;MISMATCH |

Impact analysis: **COMPLETE**

### Claims to review

- Problem file: results.csv
  - Claim: urn:rak:project:claim:main@1 (current)
  - Statement: An explicitly declared example claim
  - Declared path: urn:rak:project:artifact:results@1 → source&#95;refs → urn:rak:project:evidence:results@1 → SUPPORTS → urn:rak:project:claim:main@1

Review file availability, byte changes and declared versions before updating a baseline.
Omitted or unreached claims are not certified unaffected.

### Findings

- UNRESOLVED: CHECK&#95;IDENTITIES&#95;INCOMPLETE 
- INVALID: IDENTITY&#95;MISMATCH urn:rak:project:artifact:results@1

**Boundary:** current-byte observations and user-declared relationships only. No scientific adjudication; observations are not an atomic multi-file snapshot.


# Discovery: Irish Statute Book (irishstatutebook.ie) - Ireland

Date: 2026-06-24. **Status: CLOSED** for a grounding MVP (confirmed by live probing).

The Irish Statute Book (ISB) serves legislation as clean XML / HTML at ELI-based URLs. Keyless.
Chosen on WM's "pick the fastest" directive (DK and PT returned only HTML pages, no clean API).

## Base API properties (CONFIRMED)

- **Base URL:** `https://www.irishstatutebook.ie`
- **Authentication:** none.
- **ELI:** the URL IS the ELI: `/eli/{year}/{type}/{number}/enacted/en/{format}`.
- **Formats:** `xml` (own `legislation.dtd` schema) and `html`. (`xml` confirmed, 600 KB+ for a full act.)
- **Types:** `act` (acts), `si` (statutory instruments).

## Endpoints (CONFIRMED)

| Endpoint | Notes |
|---|---|
| `/eli/{year}/act/{number}/enacted/en/xml` | full act XML (metadata + body) |
| `/eli/{year}/act/{number}/enacted/en/html` | full act HTML |
| `/eli/{year}/si/{number}/enacted/en/{format}` | statutory instruments |

## Metadata block (CONFIRMED)

```
<act><metadata>
  <title>DATA PROTECTION ACT 2018</title>
  <number>7</number>
  <year>2018</year>
  <dateofenactment>20180524</dateofenactment>
</metadata>...
```

Parsed by regex - the act XML references an external DTD and named entities that the stdlib XML
parser would choke on; we only need this small header.

## Citation contract (Article IV) - CLOSED for IE

- `eli_uri` = `https://www.irishstatutebook.ie/eli/{year}/{type}/{number}/enacted/en`.
- `human_readable_citation` = `title` + "(No. {number} of {year})" (acts) / "(S.I. No. {n} of {year})" (SIs).
- `source_url` = the human-readable HTML page.

## Tool mapping - grounding MVP

| Tool | Endpoint |
|---|---|
| `ie_get_act` | `/eli/{year}/{type}/{number}/enacted/en/xml` (parse metadata) |
| `ie_get_text` | `/eli/{year}/{type}/{number}/enacted/en/{html\|xml}` |

**Deferred:** keyword search (ISB has no clean search API here - discover by coordinates/citation);
revised/consolidated text (separate to the enacted text).

## Differences vs the rest of the line

- The ELI is literally the request URL (no resolver, no FRBR alias to read).
- Custom XML DTD (not Akoma Ntoso) - metadata extracted by regex, not full XML parse.
- Grounding by coordinates (year + number + type), not search.

## Decision: BUILD (fast, clean XML)

ELI-as-URL, keyless, clean structured XML. Reuse: audit + cache verbatim, server pattern. New:
the ISB client + regex metadata extractor. Sixth confirmation of the line thesis.

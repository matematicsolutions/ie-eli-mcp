# Constitution of ie-eli-mcp

Version: 0.1.0
Date: 2026-06-24
Licence: Apache-2.0

`ie-eli-mcp` is an MCP server for the Irish Statute Book (`irishstatutebook.ie`), the official
source of Irish legislation. It grounds Irish acts and statutory instruments by year + number and
returns the enacted text, with verifiable ELI citations. The MVP covers the enacted text;
revised/consolidated versions are a later feature.

The 4 principles below are inherited from the `eu-legal-mcp` line Constitution (Article IV).

---

## Art. 1. Public data only

The Irish Statute Book is the official, public source of Irish legislation. The server is read-only
against it and sends nothing beyond the requested coordinates (year / number / type / format).

## Art. 2. Mandatory audit log

Every tool call MUST append one JSON line to `~/.matematic/audit/ie-eli-mcp.jsonl`
(ts / tool / input_hash SHA-256 / output_count_or_size / duration_ms / status). Inability to write =
the tool returns an error, it does not silently skip.

## Art. 3. Vendor neutrality

No tool hardcodes an LLM provider, assumes a model, or adds commercial telemetry. The server talks
only to `irishstatutebook.ie` and the local filesystem. Authentication: none; own backoff + cache.

## Art. 4. ELI citations and a human-readable citation are mandatory

Every response MUST carry three fields:
- `eli_uri`: the canonical ELI, which is the ISB URL itself
  (`https://www.irishstatutebook.ie/eli/{year}/{type}/{number}/enacted/en`).
- `human_readable_citation`: title + "(No. {number} of {year})" (acts) or the S.I. form for SIs.
- `source_url`: the human-readable HTML page of the enacted text.

---

## Open points

1. **Keyword search** - ISB has no clean search API here; discovery is by coordinates/citation.
2. **Revised (consolidated) text** - separate from the enacted text; not in this MVP.

## Ewolucja konstytucji

Changes to art. 1-4 follow SEMVER + an entry in `CHANGELOG.md` + a `pyproject.toml` bump.

First version: 2026-06-24. Author: Wieslaw Mazur / MateMatic.

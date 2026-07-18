# ie-eli-mcp

<!-- mcp-name: io.github.matematicsolutions/ie-eli-mcp -->


## Install (one command)

Published on PyPI + MCP Registry (`io.github.matematicsolutions/ie-eli-mcp`). Run without cloning:

```bash
uvx ie-eli-mcp
```

Configure your MCP client (stdio):

```json
{ "mcpServers": { "ie-eli-mcp": { "command": "uvx", "args": ["ie-eli-mcp"] } } }
```

### Windows 11 with Smart App Control

Smart App Control blocks unsigned executables, which covers `uvx.exe`, `pip.exe`
and the `ie-eli-mcp.exe` launcher that pip writes at install time. The `python.exe` and
`py.exe` from the python.org installer are signed by the Python Software
Foundation, so running the module through the interpreter works:

```bash
python -m pip install ie-eli-mcp
python -m ie_eli_mcp
```

`pip.exe` is blocked for the same reason, so install with `python -m pip`, not
`pip install`. If `python` is not on PATH, use the Windows launcher: `py -3 -m ie_eli_mcp`.

```json
{ "mcpServers": { "ie-eli-mcp": { "command": "python", "args": ["-m", "ie_eli_mcp"] } } }
```

Do not turn Smart App Control off to work around this - it cannot be re-enabled
without reinstalling Windows.

Building from source: see [Install](#install).

An MCP server for the **Irish Statute Book** (`irishstatutebook.ie`), the official source of
Irish legislation. It grounds Irish acts and statutory instruments (SIs) by year + number,
returning metadata and the full enacted text, with verifiable ELI identifiers and Irish citations.

Part of the MateMatic `eu-legal-mcp` production line - after PL, DE, AT, ES and FI. Same citation
contract, Irish Statute Book source.

> **Scope.** This MVP grounds the ENACTED text of acts and SIs by coordinates (year + number +
> type). The Irish Statute Book has no keyword-search API here, so discovery is by citation
> (Irish citations give the coordinates, e.g. "No. 7 of 2018"). Revised/consolidated versions are
> separate and not covered. Every response carries a `dataset_note`.
>
> **Licence.** Irish Statute Book content is official public information. This connector relays it
> with attribution and a `source_url`.

## The tools

| Tool | What it does |
|---|---|
| `ie_get_act` | Metadata for an act or SI by year + number + type. |
| `ie_get_text` | Full enacted text (`html` or `xml`). |

Every response carries the contract: `eli_uri` (e.g.
`https://www.irishstatutebook.ie/eli/2018/act/7/enacted/en`), `human_readable_citation`
(e.g. `DATA PROTECTION ACT 2018 (No. 7 of 2018)`), and `source_url`.

## Install

```bash
cd ie-eli-mcp
pip install -e .
```

## Configure (Claude Code / any MCP client)

```json
{
  "mcpServers": {
    "ie-eli-mcp": { "command": "ie-eli-mcp" }
  }
}
```

Environment:

- `IE_ELI_BASE_URL` - default `https://www.irishstatutebook.ie`
- `IE_ELI_CACHE_DIR` - default `~/.matematic/cache/ie-eli`
- `IE_ELI_AUDIT_DIR` - default `~/.matematic/audit`

No API key.

## Governance

- **Public data only** - read-only against the Irish Statute Book; no client data leaves the machine.
- **Audit log** - every tool call appends one JSON line to `~/.matematic/audit/ie-eli-mcp.jsonl`.
- **Vendor-neutral** - talks only to `irishstatutebook.ie`; no LLM provider, no telemetry.
- **Verifiable citations** - every response is independently checkable via `source_url`.

See `CONSTITUTION.md` and `DISCOVERY.md`.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/test_instructions_drift.py -v   # offline
pytest tests/test_smoke.py -v                # hits live Irish Statute Book
```

## Licence

Apache-2.0. © Matematic Solutions / Wieslaw Mazur.

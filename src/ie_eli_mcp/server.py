"""FastMCP entry point - Irish Statute Book tools.

Run:

    python -m ie_eli_mcp.server

Configuration via env:

- ``IE_ELI_CACHE_DIR`` (default ``~/.matematic/cache/ie-eli``)
- ``IE_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``IE_ELI_BASE_URL`` (default ``https://www.irishstatutebook.ie``)
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .audit import AuditLogger, hash_input, timer
from .citations import DOC_TYPES, build_record
from . import runtime
from .client import DEFAULT_BASE_URL, IsbClient
from .models import Act, DocType, LawText, TextFormat

INSTRUCTIONS = """\
This MCP server exposes the Irish Statute Book (irishstatutebook.ie), the official source of Irish legislation. It grounds Irish acts and statutory instruments (SIs) by year + number, returning metadata and the full ENACTED text. Every response carries a stable `eli_uri`, a `human_readable_citation` and a `source_url` (the citation contract).

## Call order

1. `ie_get_act` - metadata for an act or SI by `year`, `number` and `doc_type` (`act` or `si`). E.g. the Data Protection Act 2018 is `year=2018, number=7, doc_type=act`. Returns `eli_uri` (e.g. `https://www.irishstatutebook.ie/eli/2018/act/7/enacted/en`), title, date.
2. `ie_get_text` - the full enacted text of an act/SI, as `html` or `xml`.

## Hard constraints

- **No free-text search** - addressed by year + number + type, not keywords. You must know the coordinates (Irish citations give them, e.g. "No. 7 of 2018"). Relay the `dataset_note`.
- **ELI is the key to citability** - the ELI is the irishstatutebook.ie/eli/... URL; do not invent it.
- **Enacted text only** - revised/consolidated versions are separate and not covered here.
- **Every response has `human_readable_citation` + `source_url`** - cite both to the user.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/ie-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing or invalid (e.g. bad year, doc_type not act/si, format not html/xml).
- `not_found` - no act/SI exists for those coordinates.
- `upstream_error` - an Irish Statute Book error (HTTP, timeout). Retry once before surfacing.

## Response style

- Cite as `human_readable_citation` with the ELI URL: "DATA PROTECTION ACT 2018 (No. 7 of 2018), https://www.irishstatutebook.ie/eli/2018/act/7/enacted/en".
- NEVER invent an ELI, a number or a year - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for ie-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="ie-eli-mcp", instructions=INSTRUCTIONS)


def _base_url() -> str:
    return os.environ.get("IE_ELI_BASE_URL", runtime.base_url("eli", DEFAULT_BASE_URL)).rstrip("/")


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
        return ToolError("not_found", "No act/SI found for those coordinates in the Irish Statute Book.")
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"Irish Statute Book error: {type(exc).__name__}: {exc}")
    return exc


def _validate(year: int, number: int, doc_type: str) -> None:
    if not 1100 <= year <= 2100:
        raise ToolError("invalid_arg", f"year={year} is out of range (1100..2100).")
    if number <= 0:
        raise ToolError("invalid_arg", f"number={number} must be positive.")
    if doc_type not in DOC_TYPES:
        raise ToolError("invalid_arg", f"doc_type must be one of {DOC_TYPES}, got {doc_type!r}.")


# ---------------------------------------------------------------------------
# ie_get_act
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def ie_get_act(year: int, number: int, doc_type: DocType = "act") -> Act:
    """Fetch Irish act / SI metadata by coordinates.

    Args:
        year: e.g. ``2018``.
        number: e.g. ``7``.
        doc_type: ``"act"`` (default) or ``"si"`` (statutory instrument).

    Returns:
        ``Act`` with ``eli_uri``, ``human_readable_citation``, ``source_url``.
    """
    audit = _audit()
    _validate(year, number, doc_type)
    input_hash = hash_input({"year": year, "number": number, "doc_type": doc_type})

    with timer() as t:
        try:
            async with IsbClient(base_url=_base_url()) as client:
                xml, _ct, _url = await client.get_content(year, number, doc_type, "xml")
        except Exception as exc:
            audit.log(tool="ie_get_act", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    act = Act.model_validate(build_record(year, number, doc_type, xml))
    audit.log(tool="ie_get_act", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return act


# ---------------------------------------------------------------------------
# ie_get_text
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def ie_get_text(
    year: int, number: int, doc_type: DocType = "act", format: TextFormat = "html"
) -> LawText:
    """Fetch the full enacted text of an Irish act / SI.

    Args:
        year: e.g. ``2018``.
        number: e.g. ``7``.
        doc_type: ``"act"`` (default) or ``"si"``.
        format: ``"html"`` (default) or ``"xml"``.

    Returns:
        ``LawText`` with ``eli_uri``, ``human_readable_citation``, ``source_url`` and ``content``.
    """
    audit = _audit()
    _validate(year, number, doc_type)
    if format not in ("html", "xml"):
        raise ToolError("invalid_arg", "format must be 'html' or 'xml'.")
    input_hash = hash_input({"year": year, "number": number, "doc_type": doc_type, "format": format})

    with timer() as t:
        try:
            async with IsbClient(base_url=_base_url()) as client:
                xml, _ct, _url = await client.get_content(year, number, doc_type, "xml")
                if format == "xml":
                    content, ct, src = xml, _ct, _url
                else:
                    content, ct, src = await client.get_content(year, number, doc_type, "html")
        except Exception as exc:
            audit.log(tool="ie_get_text", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    rec = build_record(year, number, doc_type, xml)
    result = LawText(
        year=year,
        number=number,
        doc_type=doc_type,
        format=format,
        eli_uri=rec.get("eli_uri"),
        human_readable_citation=rec.get("human_readable_citation"),
        source_url=src,
        content=content,
        content_type=ct,
        byte_size=len(content.encode("utf-8")),
    )
    audit.log(tool="ie_get_text", input_hash=input_hash, output_count_or_size=result.byte_size or 0,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()

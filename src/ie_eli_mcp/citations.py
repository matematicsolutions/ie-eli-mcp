"""Irish Statute Book (ISB) citation helpers.

ISB serves legislation as XML (its own ``legislation.dtd`` schema) and HTML at ELI-based URLs:
``https://www.irishstatutebook.ie/eli/{year}/{type}/{number}/enacted/en/{format}``. The ELI is
the URL itself; the act metadata is a small block at the top of the document.

Citation contract:
- ``eli_uri``: the canonical ELI URL (``.../enacted/en``).
- ``human_readable_citation``: e.g. "DATA PROTECTION ACT 2018 (No. 7 of 2018)".
- ``source_url``: the human-readable HTML page.

The metadata is extracted by regex - the full act XML references an external DTD and named
entities, which the stdlib XML parser would choke on; we only need the simple header block.
"""

from __future__ import annotations

import re
from typing import Any

ISB_BASE = "https://www.irishstatutebook.ie"
DOC_TYPES = ("act", "si")


def eli_uri(year: int, number: int, doc_type: str = "act") -> str:
    return f"{ISB_BASE}/eli/{year}/{doc_type}/{number}/enacted/en"


def content_url(year: int, number: int, doc_type: str, fmt: str) -> str:
    return f"{ISB_BASE}/eli/{year}/{doc_type}/{number}/enacted/en/{fmt}"


def _format_date(raw: str | None) -> str | None:
    if isinstance(raw, str) and len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw


def parse_metadata(xml_text: str) -> dict[str, Any]:
    """Extract the ISB metadata header (title / number / year / date) by regex."""
    block_match = re.search(r"<metadata>(.*?)</metadata>", xml_text, re.S)
    block = block_match.group(1) if block_match else xml_text[:4000]
    out: dict[str, Any] = {}
    for tag in ("title", "number", "year", "dateofenactment"):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
        if m:
            out[tag] = m.group(1).strip()
    if "dateofenactment" in out:
        out["date_enacted"] = _format_date(out.pop("dateofenactment"))
    return out


def build_record(year: int, number: int, doc_type: str, xml_text: str) -> dict[str, Any]:
    """Combine the requested coordinates with parsed metadata into a contract-bearing record."""
    meta = parse_metadata(xml_text)
    title = meta.get("title")
    out: dict[str, Any] = {
        "year": year,
        "number": number,
        "doc_type": doc_type,
        "title": title,
        "date_enacted": meta.get("date_enacted"),
        "eli_uri": eli_uri(year, number, doc_type),
        "source_url": content_url(year, number, doc_type, "html"),
    }
    label = "No." if doc_type == "act" else "S.I. No."
    if title:
        out["human_readable_citation"] = f"{title} ({label} {number} of {year})"
    else:
        out["human_readable_citation"] = f"{label} {number} of {year}"
    return out

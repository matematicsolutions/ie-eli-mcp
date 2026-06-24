"""Pydantic v2 models for the Irish Statute Book + ie-eli-mcp."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

DocType = Literal["act", "si"]
TextFormat = Literal["xml", "html"]

DATASET_NOTE = (
    "Irish Statute Book serves the ENACTED text of acts and statutory instruments (SIs) by "
    "year + number. Discovery is by coordinates (no keyword-search API here). Revised "
    "(consolidated) versions live separately and are not covered by this MVP."
)


class _Tolerant(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Act(_Tolerant):
    """An Irish act or statutory instrument (enacted)."""

    year: int
    number: int
    doc_type: DocType = "act"
    title: str | None = None
    date_enacted: str | None = None

    # Citation contract (Art. 4 CONSTITUTION).
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    dataset_note: str = DATASET_NOTE


class LawText(_Tolerant):
    """Result of ``ie_get_text``."""

    year: int
    number: int
    doc_type: DocType = "act"
    format: TextFormat = "html"
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    content: str | None = None
    content_type: str | None = None
    byte_size: int | None = None
    dataset_note: str = DATASET_NOTE

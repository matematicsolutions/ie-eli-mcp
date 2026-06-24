"""Smoke tests - require internet, hit the live Irish Statute Book.

Run manually:

    pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import pytest

from ie_eli_mcp.server import ie_get_act, ie_get_text

# Data Protection Act 2018 - No. 7 of 2018.
YEAR, NUMBER = 2018, 7


@pytest.mark.asyncio
async def test_smoke_get_act() -> None:
    act = await ie_get_act(YEAR, NUMBER)
    assert act.eli_uri is not None and "/eli/2018/act/7" in act.eli_uri, f"bad eli: {act.eli_uri!r}"
    assert act.title is not None and "DATA PROTECTION" in act.title.upper()
    assert act.human_readable_citation is not None and "7 of 2018" in act.human_readable_citation
    assert act.date_enacted == "2018-05-24"
    assert act.source_url is not None and act.source_url.startswith("https://")


@pytest.mark.asyncio
async def test_smoke_get_text_html() -> None:
    text = await ie_get_text(YEAR, NUMBER, format="html")
    assert text.format == "html"
    assert text.content is not None and "DATA PROTECTION" in text.content.upper()
    assert text.eli_uri is not None and "/eli/2018/act/7" in text.eli_uri
    assert text.byte_size and text.byte_size > 0

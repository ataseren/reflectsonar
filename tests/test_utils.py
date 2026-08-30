"""Tests for console-safe output helpers."""

import io

from reflectsonar.report.utils import safe_print, split_code_snippet_for_reportlab


def test_safe_print_falls_back_for_non_unicode_console():
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="ascii", errors="strict")

    safe_print("Report ready \U0001f680", file=stream)
    stream.flush()

    assert raw.getvalue().decode("ascii").splitlines() == ["Report ready ?"]


def test_long_code_lines_are_wrapped_into_page_safe_chunks():
    code = ">>>   1: " + ("<p style=color:red>content</p>" * 12)

    chunks = split_code_snippet_for_reportlab(code, max_chars=40, max_lines=3)

    assert len(chunks) > 1
    assert all(len(chunk.split("<br/>")) <= 3 for chunk in chunks)
    assert "&lt;p" in "".join(chunks)
    assert all("<p style" not in chunk for chunk in chunks)

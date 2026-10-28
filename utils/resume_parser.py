"""Utilities for extracting text from text-based PDF resumes."""

from __future__ import annotations

import fitz


class ResumeParseError(ValueError):
    """Raised when a PDF cannot be read or contains no selectable text."""


def extract_pdf_text(file_bytes: bytes) -> str:
    if not file_bytes:
        raise ResumeParseError("The uploaded PDF is empty.")
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except (fitz.FileDataError, ValueError) as exc:
        raise ResumeParseError("The uploaded file is not a readable PDF.") from exc

    with document:
        pages = [page.get_text("text") for page in document]
    text = "\n".join(pages).strip()
    if not text:
        raise ResumeParseError(
            "This PDF appears to be scanned or image-only. "
            "Please upload a text-based PDF or paste the profile text."
        )
    return text

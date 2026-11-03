import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import docx
from pypdf import PdfReader


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    section: str = "General"


def extract_text_from_pdf(file_path: str) -> List[ExtractedPage]:
    """Extract page-by-page text from a PDF file with OCR fallback for scanned pages."""
    reader = PdfReader(file_path)
    pages: List[ExtractedPage] = []

    current_section = "General"
    for i, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ""
        
        # Fallback to OCR if text layer is empty/scanned
        if len(raw_text.strip()) < 30:
            try:
                import pytesseract
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, first_page=i + 1, last_page=i + 1)
                if images:
                    ocr_text = pytesseract.image_to_string(images[0])
                    if ocr_text.strip():
                        raw_text = ocr_text
            except Exception:
                pass  # Use whatever text layer was extracted

        # Check if any line resembles a section header (e.g. '1.0 Introduction' or 'Section 4: Leave Policy')
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for line in lines[:5]:
            header_match = re.match(r"^(\d+(\.\d+)*\s+[A-Za-z\s]+|[A-Z][A-Z\s]{3,}|Section\s+\d+.*|Article\s+\d+.*)$", line)
            if header_match:
                current_section = line
                break

        pages.append(
            ExtractedPage(
                page_number=i + 1,
                text=raw_text,
                section=current_section,
            )
        )

    return pages


def extract_text_from_docx(file_path: str) -> List[ExtractedPage]:
    """Extract text, section headings, and tables from a DOCX file."""
    doc = docx.Document(file_path)
    pages: List[ExtractedPage] = []

    current_section = "General"
    current_page_text = []
    page_num = 1

    # Extract paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect heading style or explicit numbered header
        if para.style.name.startswith("Heading") or re.match(r"^\d+(\.\d+)*\s+[A-Za-z]", text):
            current_section = text

        current_page_text.append(text)

        # Approximate 400 words per page if no explicit page breaks
        if len("\n".join(current_page_text).split()) > 400:
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text="\n".join(current_page_text),
                    section=current_section,
                )
            )
            page_num += 1
            current_page_text = []

    # Extract tables into formatted Markdown tables
    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            if any(cells):
                table_rows.append("| " + " | ".join(cells) + " |")

        if table_rows:
            current_page_text.append("\n" + "\n".join(table_rows) + "\n")

    if current_page_text:
        pages.append(
            ExtractedPage(
                page_number=page_num,
                text="\n".join(current_page_text),
                section=current_section,
            )
        )

    return pages


def extract_text_from_txt(file_path: str) -> List[ExtractedPage]:
    """Extract text from plain text file, splitting naturally on section headers or length limits."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    pages: List[ExtractedPage] = []
    lines = content.splitlines()

    current_section = "Overview"
    chunk_lines = []
    page_num = 1

    for line in lines:
        stripped = line.strip()
        # If this is a markdown section header and we already have accumulated text
        if stripped.startswith("#") and any(l.strip() for l in chunk_lines):
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text="\n".join(chunk_lines).strip(),
                    section=current_section,
                )
            )
            page_num += 1
            chunk_lines = []
            current_section = stripped.lstrip("#").strip()
        elif stripped.startswith("#"):
            current_section = stripped.lstrip("#").strip()

        chunk_lines.append(line)

        # Approximate 40-50 lines per page fallback
        if len(chunk_lines) >= 45:
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text="\n".join(chunk_lines).strip(),
                    section=current_section,
                )
            )
            page_num += 1
            chunk_lines = []

    if any(l.strip() for l in chunk_lines):
        pages.append(
            ExtractedPage(
                page_number=page_num,
                text="\n".join(chunk_lines).strip(),
                section=current_section,
            )
        )

    return pages


def extract_document(file_path: str, file_type: str) -> List[ExtractedPage]:
    """Extract content based on file extension/type."""
    ext = file_type.lower().lstrip(".")
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    elif ext in ["docx", "doc"]:
        return extract_text_from_docx(file_path)
    elif ext in ["txt", "md"]:
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

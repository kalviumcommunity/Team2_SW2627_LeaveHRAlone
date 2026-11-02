import re
import unicodedata
from typing import Set

# Configured regex patterns for boilerplate lines to strip
BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*Page\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*Home\s*\|\s*Products\s*\|\s*Contact\s*$", re.IGNORECASE),
    re.compile(r"^\s*Confidential\s*-\s*Internal\s+Use\s+Only\s*$", re.IGNORECASE),
]

# Standalone lines to eliminate
BOILERPLATE_LINES: Set[str] = {
    "confidential internal document",
    "confidential - internal use only",
    "all rights reserved.",
}


def remove_boilerplate(text: str) -> str:
    """Remove known page markers, headers/footers, and boilerplate lines."""
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()

        # Check regex patterns
        if any(pattern.fullmatch(stripped) for pattern in BOILERPLATE_PATTERNS):
            continue

        # Check exact lowercase lines
        if stripped.casefold() in BOILERPLATE_LINES:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_whitespace(text: str) -> str:
    """Normalize line breaks, spaces, and collapse redundant blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    normalized_lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]
    text = "\n".join(normalized_lines)

    # Collapse excessive blank lines
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def repair_line_wraps(text: str) -> str:
    """Join wrapped prose without destroying markdown headings, lists, or tables."""
    lines = text.splitlines()
    result = []

    for line in lines:
        line = line.strip()

        if not line:
            if result and result[-1] != "":
                result.append("")
            continue

        # Check if current line is structural (heading, bullet, numbered list)
        is_structural = (
            line.startswith(("#", "-", "*", "•", "|"))
            or bool(re.match(r"^\d+[.)]\s", line))
            or bool(re.match(r"^[A-Z][A-Z0-9\s:]{3,}$", line))
        )

        if (
            result
            and result[-1]
            and not is_structural
            and not result[-1].startswith(("#", "-", "*", "•", "|"))
            and not re.match(r"^\d+[.)]\s", result[-1])
        ):
            # Append to previous line with a single space
            result[-1] += " " + line
        else:
            result.append(line)

    return "\n".join(result)


def clean_text(text: str) -> str:
    """Apply the complete cleaning pipeline sequence to raw text."""
    if not isinstance(text, str):
        raise TypeError("Document content must be a string.")

    # 1. NFKC Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # 2. Boilerplate removal
    text = remove_boilerplate(text)

    # 3. Line wrap repair
    text = repair_line_wraps(text)

    # 4. Whitespace normalization
    text = normalize_whitespace(text)

    return text

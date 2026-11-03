"""
LeaveHRAlone AI — Numeric & Entitlement Hallucination Verifier
Verifies that any numbers, percentages, currency values, dates, or day/week counts
generated in the LLM answer strictly exist in the cited context chunks.
"""
import re
from typing import List, Tuple, Set


NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-four": 24, "twenty four": 24, "twenty-six": 26, "twenty six": 26,
    "thirty": 30, "sixty": 60, "ninety": 90,
}


def _extract_numeric_entities(text: str) -> Set[str]:
    """Extract numeric values, currencies, percentages, and number words from text."""
    entities = set()

    # 1. Currencies (e.g. ₹5,00,000, $1,000, Rs 500000)
    for m in re.finditer(r"(?:[\$₹€]|Rs\.?\s*)\d[\d,]*(?:\.\d+)?", text):
        clean_curr = re.sub(r"[^\d.]", "", m.group())
        if clean_curr:
            entities.add(clean_curr)

    # 2. Percentages (e.g. 100%, 80%, 2.5%)
    for m in re.finditer(r"\b\d+(?:\.\d+)?%", text):
        entities.add(m.group().replace("%", ""))

    # 3. Standard digits and numbers (e.g. 24, 1.25, 26, 12, 10)
    for m in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
        val = m.group()
        # Skip small conversational numbers (0, 1, 2) when checking strict hallucination
        entities.add(val)

    # 4. Spelled numbers
    text_lower = text.lower()
    for word, num in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", text_lower):
            entities.add(str(num))

    return entities


def verify_numeric_grounding(answer: str, context: str) -> Tuple[bool, List[str]]:
    """
    Check if all numbers present in the generated answer exist in the context.
    Returns:
        (is_grounded: bool, ungrounded_numbers: List[str])
    """
    if not answer or not context:
        return True, []

    # If the response is a standard refusal, it doesn't need numeric grounding
    if "couldn't find" in answer.lower() or "designed to help with company hr" in answer.lower():
        return True, []

    answer_numbers = _extract_numeric_entities(answer)
    context_numbers = _extract_numeric_entities(context)

    # Also extract raw text without commas to match numbers written differently
    context_normalized = re.sub(r"[,₹\$]", "", context)
    for m in re.finditer(r"\b\d+(?:\.\d+)?\b", context_normalized):
        context_numbers.add(m.group())

    ungrounded = []
    for num in answer_numbers:
        # Check direct numeric presence
        if num in context_numbers:
            continue

        # Check if the number string appears as substring anywhere in raw context
        if num in context or num in context_normalized:
            continue

        # Check float equivalence (e.g. 2 vs 2.0 or 24 vs 24.0)
        try:
            val = float(num)
            found = False
            for c_num in context_numbers:
                try:
                    if abs(float(c_num) - val) < 1e-4:
                        found = True
                        break
                except ValueError:
                    pass
            if found:
                continue
        except ValueError:
            pass

        # Skip harmless page numbers or common years (2024, 2025, 2026, 2027)
        if num in {"2024", "2025", "2026", "2027", "1", "2"}:
            continue

        ungrounded.append(num)

    is_grounded = len(ungrounded) == 0
    return is_grounded, ungrounded

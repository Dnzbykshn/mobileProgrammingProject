"""
Text normalization utilities for Turkish text search.
Extracted from: scripts/prescribe.py (keyword normalization logic)
"""


def normalize_turkish(text: str) -> str:
    """Remove Turkish special characters for accent-fuzzy matching."""
    return (
        text.replace("ş", "s")
        .replace("Ş", "S")
        .replace("ı", "i")
        .replace("İ", "I")
        .replace("ğ", "g")
        .replace("Ğ", "G")
        .replace("ü", "u")
        .replace("Ü", "U")
        .replace("ö", "o")
        .replace("Ö", "O")
        .replace("ç", "c")
        .replace("Ç", "C")
        .replace("â", "a")
        .replace("Â", "A")
        .replace("î", "i")
        .replace("Î", "I")
        .replace("û", "u")
        .replace("Û", "U")
    )


def chop_for_root(keyword: str) -> str:
    """Create a chopped version for root approximation matching."""
    normalized = normalize_turkish(keyword)
    return normalized[:-1] if len(normalized) > 3 else normalized

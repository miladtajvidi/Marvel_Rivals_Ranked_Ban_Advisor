from __future__ import annotations

import re
import unicodedata


_CONTROL_CHAR_CATEGORY_PREFIXES = ("C",)
_WHITESPACE_RE = re.compile(r"\s+")
_HIDDEN_NAME_RE = re.compile(r"^\*+\d*$")


def normalize_player_name(name: str) -> str:
    """Apply only safe normalization that cannot change lookalike characters."""

    visible_chars = [
        char
        for char in unicodedata.normalize("NFKC", name)
        if not unicodedata.category(char).startswith(_CONTROL_CHAR_CATEGORY_PREFIXES)
    ]
    return _WHITESPACE_RE.sub(" ", "".join(visible_chars)).strip()


def comparison_key(name: str) -> str:
    return normalize_player_name(name).casefold()


def is_hidden_streamer_name(name: str) -> bool:
    normalized = normalize_player_name(name)
    return bool(_HIDDEN_NAME_RE.fullmatch(normalized))


def is_exact_profile_match(requested_name: str, display_name: str) -> bool:
    return comparison_key(requested_name) == comparison_key(display_name)


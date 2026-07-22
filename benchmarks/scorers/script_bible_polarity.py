"""Polarity-aware text matching for script-bible semantic contracts."""

from __future__ import annotations

import re

NEGATION_TOKENS = {
    "can't",
    "cannot",
    "couldn't",
    "denied",
    "denies",
    "didn't",
    "doesn't",
    "false",
    "isn't",
    "never",
    "no",
    "not",
    "untrue",
    "wasn't",
    "without",
    "won't",
    "wouldn't",
}
OUTCOME_PREFIXES = (
    "beat",
    "captur",
    "conclud",
    "defeat",
    "die",
    "died",
    "end",
    "escap",
    "flee",
    "fled",
    "kill",
    "murder",
    "overpower",
    "prevail",
    "resolv",
    "shoot",
    "shot",
    "subdu",
    "triumph",
    "victor",
    "win",
    "won",
)


def _tokens(value: object) -> list[str]:
    normalized = str(value or "").lower().replace("’", "'")
    normalized = re.sub(
        r",\s*(?:and|but|yet|so|then)\b",
        " __boundary__ ",
        normalized,
    )
    normalized = re.sub(r"[.!?;]+", " __boundary__ ", normalized)
    return re.findall(r"__boundary__|[a-z0-9]+(?:'[a-z]+)?", normalized)


def _is_negated(tokens: list[str], index: int) -> bool:
    window = tokens[max(0, index - 7) : index]
    if "__boundary__" in window:
        boundary = max(index for index, token in enumerate(window) if token == "__boundary__")
        window = window[boundary + 1 :]
    if not window:
        return False
    if len(window) >= 2 and window[-2:] == ["not", "only"]:
        window = window[:-2]
    return bool(NEGATION_TOKENS & set(window)) or window[-2:] in (
        ["fails", "to"],
        ["failed", "to"],
    )


def contains_affirmed_phrase(value: object, phrase: object) -> bool:
    """Return true only when a contiguous phrase has affirmative local polarity."""
    haystack = _tokens(value)
    needle = _tokens(phrase)
    if not needle:
        return False
    for index in range(len(haystack) - len(needle) + 1):
        if haystack[index : index + len(needle)] != needle:
            continue
        if not _is_negated(haystack, index):
            return True
    return False


def regex_has_affirmed_match(pattern: str, value: str) -> bool:
    """Return true when a regex match asserts, rather than negates, its claim."""
    for match in re.finditer(pattern, value):
        prefix = _tokens(value[max(0, match.start() - 80) : match.start()])[-7:]
        match_tokens = _tokens(match.group())
        context_tokens = prefix + match_tokens
        outcome_indexes = [
            index
            for index, token in enumerate(match_tokens)
            if token.startswith(OUTCOME_PREFIXES)
        ]
        if outcome_indexes:
            if any(
                match_tokens[index] not in NEGATION_TOKENS
                and not _is_negated(context_tokens, len(prefix) + index)
                for index in outcome_indexes
            ):
                return True
            continue
        if not _is_negated(context_tokens, len(prefix)):
            return True
    return False

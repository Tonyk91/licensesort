"""Deterministic layer: regex rules for product and billing term.

A rule hit is only trusted when exactly one product matches. Zero or several
matches mean "not sure" and the line moves on to the model (or to a human).
"""

import re

from .catalog import CATALOG

_COMPILED = [(p.id, [re.compile(pat) for pat in p.patterns]) for p in CATALOG]

_TERMS = (
    ("3-year", re.compile(r"\b(?:36 ?m|36 ?mo|36 months|3 ?y|3 ?yr|3 years?|p3y)\b")),
    ("annual", re.compile(r"\b(?:annual|yearly|12 ?m|12 ?mo|12 months|1 ?y|1 ?yr|1 year|p1y)\b")),
    ("monthly", re.compile(r"\b(?:monthly|1 ?m|1 month|per month|p1m)\b")),
    ("perpetual", re.compile(r"\b(?:perpetual|perp|core pack|core license|core lic|\d+ ?c pack|core 2 pack)\b")),
)


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_products(description: str) -> list[str]:
    norm = normalize(description)
    return [pid for pid, pats in _COMPILED if any(p.search(norm) for p in pats)]


def match_product(description: str) -> str | None:
    """The single matching product id, or None if zero or several matched."""
    hits = match_products(description)
    return hits[0] if len(hits) == 1 else None


def match_term(description: str) -> str:
    norm = normalize(description)
    for term, pat in _TERMS:
        if pat.search(norm):
            return term
    return "unknown"

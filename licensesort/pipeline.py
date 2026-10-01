"""Rules first, model second, human last.

Every result says which layer decided it, so Finance can see what was matched
by a rule, what was a model's judgement, and what still needs a person.
"""

from collections.abc import Callable
from dataclasses import dataclass

from . import rules
from .catalog import UNKNOWN


@dataclass
class Result:
    product_id: str
    term: str
    source: str  # "rule" | "model" | "review"


Classifier = Callable[[str], str]


def classify_line(description: str, model: Classifier | None) -> Result:
    term = rules.match_term(description)
    pid = rules.match_product(description)
    if pid:
        return Result(pid, term, "rule")
    if model:
        pid = model(description)
        if pid != UNKNOWN:
            return Result(pid, term, "model")
    return Result(UNKNOWN, term, "review")

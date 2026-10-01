"""Compare three setups on the hand-labelled invoice lines.

    python eval.py            # rules only, model only, rules + model
    python eval.py --no-llm   # rules only (what CI runs)

The number that matters most is `wrong`: a line mapped to the wrong product goes
straight into the license count. `review` costs a person a minute; `wrong` costs
a compliance gap nobody knows about.
"""

import csv
import json
import sys
import time
from pathlib import Path

from licensesort import llm
from licensesort.catalog import UNKNOWN
from licensesort.pipeline import classify_line

ROWS = list(csv.DictReader(open(Path(__file__).parent / "data" / "invoice_lines.csv")))


def score(name: str, results: list) -> dict:
    s = {"setup": name, "lines": len(ROWS), "correct": 0, "wrong": 0, "review": 0,
         "by_rule": 0, "by_model": 0, "term_correct": 0, "errors": []}
    for row, (res, _) in zip(ROWS, results):
        gold = row["gold_product"]
        s["term_correct"] += res.term == row["gold_term"]
        s[f"by_{res.source}"] = s.get(f"by_{res.source}", 0) + 1
        if res.product_id == gold:
            s["correct"] += 1
        elif res.product_id == UNKNOWN:
            s["review"] += 1
        else:
            s["wrong"] += 1
            s["errors"].append(f'#{row["line_id"]} "{row["description"]}" -> {res.product_id} '
                               f'({res.source}), expected {gold}')
    s.pop("by_review", None)
    s["s_per_line"] = round(sum(t for _, t in results) / len(results), 3)
    return s


def run(model) -> list:
    out = []
    for row in ROWS:
        t0 = time.perf_counter()
        out.append((classify_line(row["description"], model), time.perf_counter() - t0))
    return out


def model_only(desc: str):
    from licensesort.pipeline import Result
    from licensesort.rules import match_term
    pid = llm.classify(desc)
    return Result(pid, match_term(desc), "model" if pid != UNKNOWN else "review")


def main() -> None:
    reports = [score("rules only", run(None))]
    if "--no-llm" not in sys.argv:
        llm.classify("warmup")
        timed = []
        for row in ROWS:
            t0 = time.perf_counter()
            timed.append((model_only(row["description"]), time.perf_counter() - t0))
        reports.append(score(f"model only ({llm.MODEL})", timed))
        reports.append(score(f"rules + model ({llm.MODEL})", run(llm.classify)))

    print(f"{'setup':34} {'correct':>8} {'wrong':>6} {'review':>7} {'term ok':>8} {'s/line':>7}")
    for r in reports:
        print(f"{r['setup']:34} {r['correct']:>5}/{r['lines']} {r['wrong']:>6} {r['review']:>7} "
              f"{r['term_correct']:>5}/{r['lines']} {r['s_per_line']:>7}")
    for r in reports:
        if r["errors"]:
            print(f"\nwrong answers, {r['setup']}:")
            print("\n".join("  " + e for e in r["errors"]))
    Path("results.json").write_text(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()

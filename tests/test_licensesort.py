import json

from licensesort import llm, rules
from licensesort.catalog import BY_ID, UNKNOWN
from licensesort.pipeline import classify_line


def test_normalize():
    assert rules.normalize("MSFT O365-E3 (NCE)") == "msft o365 e3 nce"
    assert rules.normalize("Slack Business+") == "slack business+"


def test_office_and_microsoft_365_are_different_products():
    assert rules.match_product("Office 365 E3 annual") == "O365-E3"
    assert rules.match_product("Microsoft 365 E3 annual") == "M365-E3"


def test_autocad_lt_is_not_autocad():
    assert rules.match_product("AutoCAD LT 2025") == "AUTOCAD-LT"
    assert rules.match_product("Autodesk AutoCAD 1Y") == "AUTOCAD"


def test_no_match_returns_none():
    assert rules.match_product("Freight & handling") is None


def test_terms():
    assert rules.match_term("renew 36M") == "3-year"
    assert rules.match_term("P1Y") == "annual"
    assert rules.match_term("NCE 1M") == "monthly"
    assert rules.match_term("SQL Svr Std 2C pack") == "perpetual"
    assert rules.match_term("Freight") == "unknown"


def test_every_catalog_id_is_in_the_model_schema():
    assert set(llm.SCHEMA["properties"]["product_id"]["enum"]) == {*BY_ID, UNKNOWN}


def test_parse_rejects_ids_outside_the_catalog():
    assert llm.parse(json.dumps({"product_id": "M365-E3"})) == "M365-E3"
    assert llm.parse(json.dumps({"product_id": "M365-E7"})) == UNKNOWN
    assert llm.parse("not json") == UNKNOWN
    assert llm.parse("[]") == UNKNOWN


def test_rule_hit_never_calls_the_model():
    def model(_):
        raise AssertionError("model called")
    assert classify_line("PBI Pro yearly", model).source == "rule"


def test_model_fills_gaps_and_unknown_goes_to_review():
    assert classify_line("Document Cloud Pro 12 mo", lambda _: "ACROBAT-PRO").source == "model"
    res = classify_line("Freight & handling", lambda _: UNKNOWN)
    assert (res.product_id, res.source) == (UNKNOWN, "review")


def test_no_model_means_review():
    assert classify_line("Freight & handling", None).source == "review"

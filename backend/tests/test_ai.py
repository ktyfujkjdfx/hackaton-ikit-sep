from app.ai.nlu.labels import LABEL_TO_INTENT, LABELS

EXPECTED = [
    "purchase_check", "forecast", "explain", "deficit_plan", "categories", "term",
    "add_spend", "add_income", "invest_advice", "credentials", "money_operation", "off_topic",
]


def test_labels_are_fixed_and_ordered():
    assert list(LABELS) == EXPECTED


def test_every_label_maps_to_contract_intent():
    intents = {
        "purchase_check", "forecast", "explain", "deficit_plan", "categories", "term",
        "add_entry", "invest_info", "refusal", "clarify", "off_topic",
    }
    assert set(LABEL_TO_INTENT) == set(LABELS)
    assert set(LABEL_TO_INTENT.values()) <= intents

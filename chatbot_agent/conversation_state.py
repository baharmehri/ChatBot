from __future__ import annotations

import copy
import json
from typing import Any, Dict, Tuple

ALLOWED_TOPICS = {
    "blood_sugar",
    "blood_pressure",
    "weight",
    "labs",
    "medication",
    "lifestyle",
    "profile",
    None,
}
ALLOWED_INTENTS = {
    "check_status",
    "record_measurement",
    "analyze",
    "explain",
    None,
}
ALLOWED_FASTING_STATUS = {"FBS", "PBS", "RBS", None}

EXPECTED_STATE_KEYS = {
    "topic",
    "intent",
    "known_fields",
    "missing_fields",
    "last_action",
}
EXPECTED_KNOWN_FIELDS_KEYS = {
    "value",
    "systolic",
    "diastolic",
    "fasting_status",
    "date",
}


def default_conversation_state() -> Dict[str, Any]:
    return {
        "topic": None,
        "intent": None,
        "known_fields": {
            "value": None,
            "systolic": None,
            "diastolic": None,
            "fasting_status": None,
            "date": None,
        },
        "missing_fields": [],
        "last_action": None,
    }


def validate_conversation_state(state: Any) -> bool:
    if not isinstance(state, dict):
        return False
    if set(state.keys()) != EXPECTED_STATE_KEYS:
        return False

    if state.get("topic") not in ALLOWED_TOPICS:
        return False
    if state.get("intent") not in ALLOWED_INTENTS:
        return False

    known_fields = state.get("known_fields")
    if not isinstance(known_fields, dict):
        return False
    if set(known_fields.keys()) != EXPECTED_KNOWN_FIELDS_KEYS:
        return False

    if known_fields["fasting_status"] not in ALLOWED_FASTING_STATUS:
        return False

    missing_fields = state.get("missing_fields")
    if not isinstance(missing_fields, list):
        return False
    if not all(isinstance(item, str) for item in missing_fields):
        return False

    last_action = state.get("last_action")
    if last_action is not None and not isinstance(last_action, str):
        return False

    return True


def merge_conversation_state(
    previous: Dict[str, Any], proposed: Dict[str, Any]
) -> Dict[str, Any]:
    merged = copy.deepcopy(proposed)
    for key in ("topic", "intent", "last_action"):
        if merged.get(key) is None and previous.get(key) is not None:
            merged[key] = previous.get(key)

    merged_known_fields = merged.get("known_fields", {})
    previous_known_fields = previous.get("known_fields", {})
    for field, previous_value in previous_known_fields.items():
        if merged_known_fields.get(field) is None and previous_value is not None:
            merged_known_fields[field] = previous_value
    merged["known_fields"] = merged_known_fields
    return merged


def extract_response_and_state(
    llm_output: str, previous_state: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    response_text = llm_output.strip()
    new_state = copy.deepcopy(previous_state)

    if "RESPONSE:" not in llm_output or "STATE:" not in llm_output:
        return response_text, new_state

    response_section = llm_output.split("RESPONSE:", 1)[1]
    response_body, state_section = response_section.split("STATE:", 1)
    response_text = response_body.strip() or response_text

    state_start = state_section.find("{")
    state_end = state_section.rfind("}")
    if state_start == -1 or state_end == -1 or state_end <= state_start:
        return response_text, new_state

    state_payload = state_section[state_start:state_end + 1].strip()
    try:
        parsed_state = json.loads(state_payload)
    except json.JSONDecodeError:
        return response_text, new_state

    if not validate_conversation_state(parsed_state):
        return response_text, new_state

    return response_text, merge_conversation_state(previous_state, parsed_state)


def serialize_state(state: Dict[str, Any]) -> str:
    return json.dumps(state, ensure_ascii=True, separators=(",", ": "))

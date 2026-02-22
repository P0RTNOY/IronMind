import re
from typing import Any, Set

_REDACTED_STR = "***redacted***"

# Simple substring check (e.g. key contains 'cvv')
def _is_sensitive_key(key: str, redact_keys: Set[str]) -> bool:
    lk = key.lower()
    return any(rk in lk for rk in redact_keys)

def _is_sensitive_value(key: str, value: str) -> bool:
    """
    Heuristics to redact values that look like PANs or CVVs 
    even if the key name dodged the substring match.
    """
    if not isinstance(value, str):
        return False
        
    v_clean = value.replace(" ", "").replace("-", "")
    
    # Heuristic 1: Looks like a PAN (13-19 digits)
    if v_clean.isdigit() and 13 <= len(v_clean) <= 19:
        return True
        
    # Heuristic 2: Looks like a CVV (3-4 digits under a lightly suspicious key)
    lk = key.lower()
    if v_clean.isdigit() and len(v_clean) in (3, 4):
        if "cv" in lk or "sec" in lk or "code" in lk:
            return True

    return False

def redact_payload(obj: Any, redact_keys: Set[str], max_depth: int = 6, current_depth: int = 0) -> Any:
    """
    Recursively traverse a dict/list and redact PII based on key substrings or value heuristics.
    Truncates strings longer than 500 chars to prevent massive log dumps.
    """
    if current_depth > max_depth:
        return "***max_depth_exceeded***"

    if isinstance(obj, dict):
        redacted_dict = {}
        for k, v in obj.items():
            k_str = str(k)
            # 1. Match explicitly banned keys
            if _is_sensitive_key(k_str, redact_keys):
                redacted_dict[k] = _REDACTED_STR
            # 2. Match heuristic values
            elif isinstance(v, str) and _is_sensitive_value(k_str, v):
                redacted_dict[k] = _REDACTED_STR
            # 3. Recurse
            else:
                redacted_dict[k] = redact_payload(v, redact_keys, max_depth, current_depth + 1)
        return redacted_dict

    elif isinstance(obj, list):
        return [redact_payload(item, redact_keys, max_depth, current_depth + 1) for item in obj]

    elif isinstance(obj, str):
        if len(obj) > 500:
            return obj[:200] + "...(truncated)"
        return obj

    # Ints, bools, floats, None pass through
    return obj

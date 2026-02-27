import json
import os

def load_json_fixture(rel_path: str) -> dict:
    """
    Loads a JSON fixture relative to the tests/fixtures directory.
    Example: load_json_fixture("payplus/approved.json")
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fixture_path = os.path.join(base_dir, "fixtures", rel_path)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

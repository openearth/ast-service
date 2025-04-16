from pytest import fixture
import json
from pathlib import Path

@fixture
def feature_collection() -> dict:
    fp = Path(__file__).parent.parent / "test"/ "test_heatstress_reduction.json"
    with open(fp, "r") as f:
        data = json.load(f)
    return data["data"]

import pandas as pd

from src.normalize.cleaning import apply_normalization, normalize_manufacturer, normalize_model


def test_manufacturer_variants():
    assert normalize_manufacturer("Allen Bradley") == "Allen-Bradley"
    assert normalize_manufacturer("CISCO") == "Cisco"
    assert normalize_manufacturer("Microtik") == "MikroTik"


def test_model_normalization_unknowns():
    assert normalize_model(" 1756-L83E ") == "1756-L83E"
    assert normalize_model("Unknown") is None


def test_apply_normalization_sets_review_required():
    df = pd.DataFrame(
        {
            "manufacturer_raw": ["Dell", "Unknown"],
            "model_raw": ["R740", None],
            "component_type_raw": ["server", "PLC"],
            "name": ["Main station", "Main station"],
        }
    )
    out = apply_normalization(df)
    assert out.loc[0, "review_required"] == 0
    assert out.loc[1, "review_required"] == 1

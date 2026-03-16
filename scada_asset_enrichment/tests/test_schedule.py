import pandas as pd

from src.schedule.maintenance import generate_schedule


def test_schedule_uses_fallback_and_flags_missing_date():
    assets = pd.DataFrame(
        [
            {
                "asset_id": 1,
                "manufacturer_normalized": "Cisco",
                "model_normalized": "IE2000",
                "component_type_normalized": "Network Switch",
                "install_date": "2024-01-01",
                "last_service_date": None,
            },
            {
                "asset_id": 2,
                "manufacturer_normalized": "Cisco",
                "model_normalized": "IE3000",
                "component_type_normalized": "Network Switch",
                "install_date": None,
                "last_service_date": None,
            },
        ]
    )
    products = pd.DataFrame(
        [
            {
                "product_id": 10,
                "manufacturer_normalized": "Cisco",
                "model_normalized": "IE2000",
                "component_type_normalized": "Network Switch",
                "service_interval_days": None,
                "service_interval_months": None,
                "legacy_flag": 0,
                "end_of_life_flag": 0,
            },
            {
                "product_id": 11,
                "manufacturer_normalized": "Cisco",
                "model_normalized": "IE3000",
                "component_type_normalized": "Network Switch",
                "service_interval_days": None,
                "service_interval_months": None,
                "legacy_flag": 0,
                "end_of_life_flag": 0,
            },
        ]
    )
    fallback = pd.DataFrame(
        [
            {
                "component_type_normalized": "Network Switch",
                "service_interval_days": 180,
                "service_interval_months": 6,
                "maintenance_basis": "time_based",
                "maintenance_tasks": "check ports",
                "technician_type": "network_engineer",
            }
        ]
    )

    schedule, review = generate_schedule(assets, products, fallback)
    assert len(schedule) == 1
    assert schedule.loc[0, "asset_id"] == 1
    assert len(review) == 1
    assert review.loc[0, "issue_code"] == "missing_base_date"

from app.services.scoring import asset_risk_score, project_score


def test_asset_risk_score_deterministic():
    asset = {"condition_score": 60, "cyber_notes": "weak", "asset_type": "PLC"}
    assert asset_risk_score(asset) == 68.0


def test_project_score_deterministic():
    p = {"risk_impact": 4, "risk_likelihood": 3, "total_cost": 300000, "urgency": 6, "dependencies": "", "resource_internal_fte": 2, "resource_external_fte": 1}
    assert project_score(p) == 95.4

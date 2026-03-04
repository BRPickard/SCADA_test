from app.services.scenario import run_scenario


def test_scenario_respects_budget_caps():
    projects = [
        {"id": 1, "name": "P1", "total_cost": 300, "resource_internal_fte": 2, "year": "2026", "risk_impact": 5, "risk_likelihood": 5},
        {"id": 2, "name": "P2", "total_cost": 400, "resource_internal_fte": 2, "year": "2026", "risk_impact": 4, "risk_likelihood": 4},
    ]
    out = run_scenario(projects, {"budget_caps": {"2026": 500}})
    assert len(out["selected"]) == 1

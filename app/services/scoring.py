def asset_risk_score(asset: dict, weights: dict | None = None) -> float:
    w = weights or {"condition": 0.45, "cyber": 0.3, "criticality": 0.25}
    condition_component = max(0, 100 - float(asset.get("condition_score", 50)))
    cyber_component = 100 if asset.get("cyber_notes") else 20
    criticality_component = 80 if "PLC" in (asset.get("asset_type") or "") else 50
    return round(
        condition_component * w["condition"]
        + cyber_component * w["cyber"]
        + criticality_component * w["criticality"],
        2,
    )


def project_score(project: dict, weights: dict | None = None) -> float:
    w = weights or {
        "risk_reduction": 0.35,
        "cost": 0.2,
        "urgency": 0.2,
        "readiness": 0.15,
        "resource_feasibility": 0.1,
    }
    risk_reduction = float(project.get("risk_impact", 1)) * float(project.get("risk_likelihood", 1)) * 10
    cost_penalty = max(1, float(project.get("total_cost", 1)) / 100000)
    urgency = float(project.get("urgency", 5)) * 10
    readiness = 100 if not project.get("dependencies") else 65
    res = max(0, 100 - (float(project.get("resource_internal_fte", 0)) + float(project.get("resource_external_fte", 0))) * 10)
    return round(risk_reduction * w["risk_reduction"] + (100 - cost_penalty) * w["cost"] + urgency * w["urgency"] + readiness * w["readiness"] + res * w["resource_feasibility"], 2)

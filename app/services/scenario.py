from collections import defaultdict
from app.services.scoring import project_score


def run_scenario(projects: list[dict], settings: dict) -> dict:
    budget_caps = settings.get("budget_caps", {})
    staffing_caps = settings.get("staffing_caps", {})
    must_do = set(settings.get("must_do", []))
    defer = set(settings.get("defer", []))

    ranked = sorted(projects, key=lambda p: project_score(p, settings.get("project_weights")), reverse=True)
    selected = []
    annual_cost = defaultdict(float)
    annual_staff = defaultdict(float)

    for p in ranked:
        pid = str(p["id"])
        year = str(p.get("year", "2026"))
        if pid in defer:
            continue
        cost = float(p.get("total_cost", 0))
        staff = float(p.get("resource_internal_fte", 0))
        budget_ok = annual_cost[year] + cost <= float(budget_caps.get(year, 1e18))
        staff_ok = annual_staff[year] + staff <= float(staffing_caps.get(year, 1e18))
        if pid in must_do or (budget_ok and staff_ok):
            selected.append({**p, "score": project_score(p, settings.get("project_weights"))})
            annual_cost[year] += cost
            annual_staff[year] += staff

    return {
        "selected": selected,
        "annual_cost": dict(annual_cost),
        "annual_staff": dict(annual_staff),
    }

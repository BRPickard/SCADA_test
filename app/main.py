from datetime import datetime
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.db import Base, engine, get_db
from app.models import Asset, Project, Scenario, SourceMapping, SourceSystem, SyncRun, User
from app.security import hash_password, verify_password
from app.services.scoring import asset_risk_score
from app.services.scenario import run_scenario
from app.services.sync import sync_source, connector_for

app = FastAPI(title="Dynamic SCADA Master Plan Tool")
app.add_middleware(SessionMiddleware, secret_key="change-me")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
scheduler = BackgroundScheduler()


def current_user(request: Request, db: Session) -> User | None:
    uid = request.session.get("uid")
    if not uid:
        return None
    return db.query(User).get(uid)


def require_role(request: Request, db: Session, allowed: set[str]):
    user = current_user(request, db)
    if not user or user.role not in allowed:
        return None
    return user


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    if not db.query(User).filter_by(username="admin").first():
        db.add(User(username="admin", password_hash=hash_password("admin"), role="Admin"))
    if not db.query(Scenario).filter_by(name="good").first():
        db.add_all([
            Scenario(name="good", settings_json={"budget_caps": {"2026": 500000}, "staffing_caps": {"2026": 8}}),
            Scenario(name="better", settings_json={"budget_caps": {"2026": 750000}, "staffing_caps": {"2026": 12}}),
            Scenario(name="best", settings_json={"budget_caps": {"2026": 1200000}, "staffing_caps": {"2026": 16}}),
        ])
    db.commit()
    scheduler.add_job(run_scheduled_syncs, "interval", minutes=10)
    scheduler.start()


def run_scheduled_syncs():
    db = next(get_db())
    for source in db.query(SourceSystem).filter_by(enabled=True).all():
        sync_source(db, source)


@app.get("/", response_class=HTMLResponse)
def landing(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    assets = db.query(Asset).count()
    projects = db.query(Project).count()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "assets": assets, "projects": projects})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.password_hash):
        request.session["uid"] = user.id
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.get("/assets", response_class=HTMLResponse)
def assets(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(Asset)
    if q:
        query = query.filter(Asset.asset_type.contains(q))
    rows = query.limit(200).all()
    enriched = [{"obj": a, "risk": a.risk_override if a.risk_override is not None else asset_risk_score(a.__dict__)} for a in rows]
    return templates.TemplateResponse("assets.html", {"request": request, "assets": enriched, "q": q})


@app.get("/roadmap", response_class=HTMLResponse)
def roadmap(request: Request, scenario_id: int | None = None, db: Session = Depends(get_db)):
    scenarios = db.query(Scenario).all()
    projects = db.query(Project).all()
    selected_scenario = scenarios[0] if scenarios else None
    if scenario_id:
        selected_scenario = db.query(Scenario).get(scenario_id)
    output = run_scenario([{"id": p.id, "name": p.name, "total_cost": p.total_cost, "resource_internal_fte": p.resource_internal_fte, "dependencies": p.dependencies, "year": str((p.start_date.year if p.start_date else 2026)), "risk_impact": p.risk_impact, "risk_likelihood": p.risk_likelihood} for p in projects], selected_scenario.settings_json if selected_scenario else {})
    return templates.TemplateResponse("roadmap.html", {"request": request, "scenarios": scenarios, "selected_scenario": selected_scenario, "output": output})


@app.get("/sources", response_class=HTMLResponse)
def sources_page(request: Request, db: Session = Depends(get_db)):
    sources = db.query(SourceSystem).all()
    logs = db.query(SyncRun).order_by(SyncRun.started_at.desc()).limit(20).all()
    mappings = db.query(SourceMapping).all()
    return templates.TemplateResponse("sources.html", {"request": request, "sources": sources, "logs": logs, "mappings": mappings})


@app.post("/sources")
def add_source(name: str = Form(...), connector_type: str = Form(...), endpoint: str = Form(""), cadence_minutes: int = Form(60), mock_mode: bool = Form(True), db: Session = Depends(get_db)):
    auth_json = {"mock_mode": mock_mode, "feature_layer_url": endpoint, "portal_url": endpoint}
    db.add(SourceSystem(name=name, connector_type=connector_type, endpoint=endpoint, cadence_minutes=cadence_minutes, auth_json=auth_json))
    db.commit()
    return RedirectResponse("/sources", status_code=303)


@app.post("/sources/{source_id}/test")
def test_source(source_id: int, db: Session = Depends(get_db)):
    src = db.query(SourceSystem).get(source_id)
    ok, msg = connector_for(src).test_connection()
    return {"ok": ok, "message": msg}


@app.post("/sources/{source_id}/sync")
def manual_sync(source_id: int, db: Session = Depends(get_db)):
    src = db.query(SourceSystem).get(source_id)
    sync_source(db, src)
    return RedirectResponse("/sources", status_code=303)

@app.get('/projects', response_class=HTMLResponse)
def projects_page(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    scored = [{"obj": p, "score": __import__('app.services.scoring', fromlist=['project_score']).project_score(p.__dict__)} for p in projects]
    return templates.TemplateResponse('projects.html', {"request": request, "projects": scored})


@app.get('/scenarios', response_class=HTMLResponse)
def scenarios_page(request: Request, db: Session = Depends(get_db)):
    scenarios = db.query(Scenario).all()
    projects = db.query(Project).all()
    comparison = []
    for s in scenarios:
        out = run_scenario([{"id": p.id, "name": p.name, "total_cost": p.total_cost, "resource_internal_fte": p.resource_internal_fte, "year": str((p.start_date.year if p.start_date else 2026)), "risk_impact": p.risk_impact, "risk_likelihood": p.risk_likelihood} for p in projects], s.settings_json)
        comparison.append({"scenario": s, "count": len(out['selected']), "cost": sum(out['annual_cost'].values())})
    return templates.TemplateResponse('scenarios.html', {"request": request, "scenarios": scenarios, "comparison": comparison})


@app.post('/scenarios')
def create_scenario(name: str = Form(...), budget_cap: float = Form(500000), staffing_cap: float = Form(8), db: Session = Depends(get_db)):
    db.add(Scenario(name=name, settings_json={"budget_caps": {"2026": budget_cap}, "staffing_caps": {"2026": staffing_cap}}, created_by="admin"))
    db.commit()
    return RedirectResponse('/scenarios', status_code=303)


@app.get('/admin', response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse('admin.html', {"request": request, "users": users})


@app.post("/sources/{source_id}/mappings")
def add_mapping(source_id: int, entity_name: str = Form(...), source_field: str = Form(...), target_field: str = Form(...), db: Session = Depends(get_db)):
    db.add(SourceMapping(source_system_id=source_id, entity_name=entity_name, source_field=source_field, target_field=target_field))
    db.commit()
    return RedirectResponse('/sources', status_code=303)

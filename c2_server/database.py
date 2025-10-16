# DΞMON CORE: The Swarm's Memory
# Manages the state of assets and targets.

import sqlite3
import random
import time
from models import AssetRegistration, Target, TaskResult

DB_FILE = "swarm_assets.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Assets: The soldiers in the swarm
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            proxy TEXT NOT NULL,
            status TEXT DEFAULT 'dormant', -- dormant, active, cooldown
            health TEXT DEFAULT 'healthy', -- healthy, flagged, banned
            trust_score INTEGER DEFAULT 50, -- Heuristic value
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        # Targets: The list of the damned
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            phone_number TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending', -- pending, under_attack, verification, terminated, resilient
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP
        )
        ''')
        conn.commit()

def register_asset_db(asset: AssetRegistration):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO assets (session_id, proxy) VALUES (?, ?)", (asset.session_id, asset.proxy))
            conn.commit()
        return {"status": "Asset registered successfully."}
    except sqlite3.IntegrityError:
        return {"status": "Asset already exists."}

def add_target_db(target: Target):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO targets (phone_number, status) VALUES (?, 'pending')", (target.phone_number,))
            conn.commit()
        return {"status": "Target acquired. Awaiting judgment."}
    except sqlite3.IntegrityError:
        return {"status": "Target already in sights."}

def get_task_for_asset(session_id: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find a healthy, dormant asset
        cursor.execute("SELECT * FROM assets WHERE session_id = ? AND health = 'healthy' AND status = 'dormant'", (session_id,))
        asset = cursor.fetchone()
        if not asset:
            return {"task": "cooldown", "duration": 300} # Not ready or not found

        # Priority 1: Verification tasks
        cursor.execute("SELECT * FROM targets WHERE status = 'verification' ORDER BY last_verified ASC LIMIT 1")
        target_to_verify = cursor.fetchone()
        if target_to_verify:
            cursor.execute("UPDATE assets SET status = 'active', last_active = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
            conn.commit()
            return {"task": "verify_target", "target_number": target_to_verify['phone_number']}

        # Priority 2: New attacks
        cursor.execute("SELECT * FROM targets WHERE status IN ('pending', 'under_attack') ORDER BY added_at ASC LIMIT 1")
        target_to_attack = cursor.fetchone()
        if target_to_attack:
            cursor.execute("UPDATE assets SET status = 'active', last_active = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
            cursor.execute("UPDATE targets SET status = 'under_attack' WHERE phone_number = ?", (target_to_attack['phone_number'],))
            conn.commit()
            
            # Diversify attack vectors
            attack_type = random.choice(["report_spam", "report_spam", "group_poison"]) # Weight spam reports more heavily
            return {"task": attack_type, "target_number": target_to_attack['phone_number']}

    # No active targets, go to cooldown
    return {"task": "cooldown", "duration": 600}

def update_asset_status_db(result: TaskResult):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Default status is cooldown
        new_status = 'cooldown'
        health_change = 0

        if result.outcome == 'success':
            health_change = 1 # Reward success
        elif result.outcome == 'failure':
            health_change = -5 # Punish failure
        elif result.outcome == 'banned':
            new_status = 'banned' # Asset is burned
            health_change = -100
        
        cursor.execute(
            "UPDATE assets SET status = ?, trust_score = trust_score + ?, health = CASE WHEN trust_score + ? <= 0 THEN 'banned' ELSE health END WHERE session_id = ?",
            (new_status, health_change, health_change, result.session_id)
        )
        conn.commit()

def update_target_status_db(result: TaskResult):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if result.task_type == "verify_target":
            new_status = 'resilient' # Assume it survived
            if result.outcome == 'terminated':
                new_status = 'terminated' # Confirmed kill
            
            cursor.execute("UPDATE targets SET status = ?, last_verified = CURRENT_TIMESTAMP WHERE phone_number = ?", (new_status, result.target_number))
        elif result.task_type in ["report_spam", "group_poison"] and result.outcome == 'success':
            # After a successful attack, queue it for verification
            cursor.execute("UPDATE targets SET status = 'verification' WHERE phone_number = ?", (result.target_number,))
        
        conn.commit()
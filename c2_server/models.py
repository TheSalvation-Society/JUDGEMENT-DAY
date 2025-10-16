# DΞMON CORE: C2 DATA MODELS v1.0
# The very soul of the assets and targets, given form.

from pydantic import BaseModel
from typing import Optional
import time

class Task(BaseModel):
    """Defines the structure of a task sent to a Stinger asset."""
    task: str # e.g., 'report_spam', 'verify_target', 'cooldown'
    target_number: Optional[str] = None
    duration: Optional[int] = None # For cooldown tasks

class ResultSubmission(BaseModel):
    """Defines the structure of a result received from a Stinger asset."""
    session_id: str
    target_number: str
    task_type: str
    outcome: str # e.g., 'success', 'failure', 'terminated', 'banned', 'unresponsive'

class Asset:
    """In-memory representation of a Stinger client."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.last_seen: float = time.time()
        self.status: str = "active" # active, banned, unresponsive
        self.tasks_completed: int = 0
        self.failures: int = 0
        self.proxy: Optional[str] = None

class Target:
    """In-memory representation of a report target."""
    def __init__(self, number: str):
        self.number = number
        self.status: str = "pending" # pending, assigned, terminated, resilient, verifying
        self.reports_received: int = 0
        self.last_updated: float = time.time()
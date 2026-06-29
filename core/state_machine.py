import logging
import sqlite3
import json
from datetime import datetime
from typing import Optional
from core.event_bus import event_bus, StateTransition
from memory.db import DatabaseManager

logger = logging.getLogger(__name__)

class StateMachine:
    """
    Manages the authoritative state of the engagement and persists it for crash recovery.
    """
    STATES = {
        "IDLE", "PLANNING", "EXECUTING", "WAITING", "VERIFYING", 
        "ESCALATING", "SUMMARIZING", "REPLANNING", "DONE", "FAILED"
    }

    def __init__(self, db_manager: DatabaseManager, engagement_id: str):
        self.db = db_manager
        self.engagement_id = engagement_id
        self.current_state = "IDLE"
        self._load_or_init_state()

    def _load_or_init_state(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT state FROM engagement_state WHERE engagement_id = ?",
                    (self.engagement_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    self.current_state = row["state"]
                    logger.info(f"Loaded existing state: {self.current_state}")
                else:
                    self.current_state = "IDLE"
                    cursor.execute(
                        """
                        INSERT INTO engagement_state 
                        (engagement_id, state, prev_state, entered_at) 
                        VALUES (?, ?, ?, ?)
                        """,
                        (self.engagement_id, "IDLE", None, datetime.utcnow())
                    )
                    conn.commit()
                    logger.info("Initialized new engagement state: IDLE")
        except sqlite3.Error as e:
            logger.error(f"Failed to load/init state: {e}")
            raise

    def transition(self, to_state: str, trigger: str, context_snap: Optional[dict] = None) -> bool:
        if to_state not in self.STATES:
            logger.error(f"Invalid state transition attempted: {to_state}")
            return False
            
        prev_state = self.current_state
        logger.info(f"State transition: {prev_state} -> {to_state} (Trigger: {trigger})")
        
        self.current_state = to_state
        
        # Persist the transition
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE engagement_state 
                    SET state = ?, prev_state = ?, entered_at = ?, context_snap = ?
                    WHERE engagement_id = ?
                    """,
                    (
                        to_state, 
                        prev_state, 
                        datetime.utcnow(), 
                        json.dumps(context_snap) if context_snap else None,
                        self.engagement_id
                    )
                )
                conn.commit()
                
            # Emit transition event
            event_bus.emit(StateTransition(
                from_state=prev_state,
                to_state=to_state,
                trigger=trigger
            ))
            
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to persist state transition: {e}")
            return False

    def recover(self):
        """
        Crash recovery entrypoint.
        """
        logger.info(f"Attempting crash recovery for engagement {self.engagement_id} from state {self.current_state}")
        # Logic to resume execution based on self.current_state
        if self.current_state in ["EXECUTING", "WAITING"]:
            logger.info("Resuming execution...")
            # Trigger execution resumption
            self.transition("EXECUTING", "crash_recovery")

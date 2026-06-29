import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "memory/findings.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # State tracking
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS engagement_state (
                    engagement_id  TEXT PRIMARY KEY,
                    state          TEXT NOT NULL,
                    prev_state     TEXT,
                    entered_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_snap   TEXT,
                    checkpoint_id  TEXT
                )
                """)

                # Asset inventory
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS hosts (
                    id          INTEGER PRIMARY KEY,
                    engagement_id TEXT,
                    ip          TEXT NOT NULL,
                    hostname    TEXT,
                    os_guess    TEXT,
                    status      TEXT DEFAULT 'active',
                    first_seen  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes       TEXT
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id          INTEGER PRIMARY KEY,
                    host_id     INTEGER REFERENCES hosts(id),
                    port        INTEGER,
                    protocol    TEXT,
                    service     TEXT,
                    version     TEXT,
                    banner      TEXT,
                    tls         BOOLEAN
                )
                """)

                # Findings & Execution
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id          INTEGER PRIMARY KEY,
                    host_id     INTEGER REFERENCES hosts(id),
                    service_id  INTEGER REFERENCES services(id),
                    title       TEXT NOT NULL,
                    severity    TEXT CHECK(severity IN ('critical','high','medium','low','info')),
                    cvss_score  REAL,
                    cve         TEXT,
                    description TEXT,
                    evidence    TEXT,
                    remediation TEXT,
                    status      TEXT DEFAULT 'open',
                    confirmed   BOOLEAN DEFAULT FALSE,
                    artifact_hash TEXT,
                    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          TEXT PRIMARY KEY,
                    engagement_id TEXT,
                    status      TEXT,
                    task_json   TEXT,
                    result_json TEXT,
                    created_at  DATETIME,
                    completed_at DATETIME
                )
                """)

                # Advanced context
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS attack_paths (
                    id          INTEGER PRIMARY KEY,
                    from_host   INTEGER REFERENCES hosts(id),
                    to_host     INTEGER REFERENCES hosts(id),
                    technique   TEXT,
                    description TEXT,
                    exploited   BOOLEAN DEFAULT FALSE
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id          INTEGER PRIMARY KEY,
                    host_id     INTEGER REFERENCES hosts(id),
                    username    TEXT,
                    secret_type TEXT,
                    secret_hash TEXT,
                    vault_ref   TEXT
                )
                """)
                
                conn.commit()
                logger.info(f"Database initialized successfully at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

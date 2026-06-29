import logging
import json
import os
from agents.supervisor import BaseAgent
from core.event_bus import Event, StateTransition
from memory.db import DatabaseManager

logger = logging.getLogger(__name__)

class ReportAgent(BaseAgent):
    name = "ReportAgent"
    subscribes_to = [StateTransition]

    def __init__(self, db_manager: DatabaseManager, workspace_root: str = "workspaces"):
        self.db = db_manager
        self.workspace_root = workspace_root

    def handle(self, event: Event) -> None:
        if isinstance(event, StateTransition):
            if event.to_state == "DONE":
                self.generate_reports("eng-2025-042")

    def generate_reports(self, engagement_id: str) -> None:
        logger.info(f"Generating reports for engagement: {engagement_id}")
        report_dir = os.path.join(self.workspace_root, engagement_id, "report")
        os.makedirs(report_dir, exist_ok=True)
        
        findings = self._fetch_findings(engagement_id)
        
        self._generate_json(findings, os.path.join(report_dir, "findings.json"))
        self._generate_markdown(findings, os.path.join(report_dir, "report.md"))
        self._generate_html(findings, os.path.join(report_dir, "report.html"))
        
        logger.info(f"Reports successfully generated in {report_dir}")

    def _fetch_findings(self, engagement_id: str) -> list:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT f.*, h.ip, h.hostname, s.port, s.protocol
                    FROM findings f
                    JOIN hosts h ON f.host_id = h.id
                    LEFT JOIN services s ON f.service_id = s.id
                    WHERE h.engagement_id = ?
                    ORDER BY
                        CASE severity 
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                            WHEN 'info' THEN 5
                            ELSE 6
                        END
                    """, 
                    (engagement_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to fetch findings for report: {e}")
            return []

    def _generate_json(self, findings: list, path: str):
        with open(path, "w") as f:
            json.dump({"findings": findings}, f, indent=2)

    def _generate_markdown(self, findings: list, path: str):
        with open(path, "w") as f:
            f.write("# Penetration Test Report\n\n")
            f.write("## Findings Summary\n\n")
            for finding in findings:
                f.write(f"### [{finding['severity'].upper()}] {finding['title']}\n")
                f.write(f"- **Asset**: {finding['ip']}:{finding['port']}\n")
                f.write(f"- **Description**: {finding['description']}\n\n")

    def _generate_html(self, findings: list, path: str):
        # A full implementation would use Jinja2. This is a skeletal HTML generation.
        with open(path, "w") as f:
            f.write("<html><body><h1>Penetration Test Report</h1></body></html>")

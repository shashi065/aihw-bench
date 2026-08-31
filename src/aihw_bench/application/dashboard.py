"""Static interactive dashboard generation for stored benchmark sessions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from html import escape
from importlib.resources import files
from pathlib import Path
from typing import Any, Protocol

from aihw_bench.application.assistant import BenchmarkAssistant
from aihw_bench.domain.models import BenchmarkSession
from aihw_bench.utils.hashing import sha256_file
from aihw_bench.utils.paths import ensure_directory, resolve_within

DASHBOARD_DOCUMENTATION = "docs/user-guide/dashboard.md"
DEFAULT_MAX_SESSIONS = 200


class SessionReader(Protocol):
    """Minimal session-store contract used by dashboard generation."""

    def list_sessions(self) -> list[str]: ...

    def load(self, session_id: str) -> BenchmarkSession: ...


@dataclass(frozen=True, slots=True)
class DashboardArtifact:
    """Generated standalone dashboard artifact."""

    path: Path
    session_count: int
    sha256: str


class DashboardService:
    """Build a responsive dashboard from a bounded page of stored sessions."""

    def __init__(self, *, max_sessions: int = DEFAULT_MAX_SESSIONS) -> None:
        if max_sessions <= 0:
            raise ValueError("max_sessions must be positive")
        self.max_sessions = max_sessions

    def build(
        self, store: SessionReader, output_dir: Path, *, title: str = "AIHW-Bench Dashboard"
    ) -> DashboardArtifact:
        """Generate a dashboard without embedding an unbounded history payload."""
        session_ids = store.list_sessions()[-self.max_sessions :]
        sessions: list[BenchmarkSession] = []
        for session_id in session_ids:
            try:
                sessions.append(store.load(session_id))
            except Exception:
                # One damaged historical session must not prevent access to valid ones.
                continue
        payload = {"sessions": [self._session_payload(session) for session in sessions]}
        root = ensure_directory(output_dir)
        asset_root = ensure_directory(root / "assets")
        for asset in ("dashboard.css", "dashboard.js"):
            target = resolve_within(asset_root, asset_root / asset)
            target.write_text(
                files("aihw_bench.presentation.assets").joinpath(asset).read_text(encoding="utf-8"),
                encoding="utf-8",
                newline="",
            )
        path = resolve_within(root, root / "index.html")
        path.write_text(
            _render_dashboard(title, payload, len(session_ids)), encoding="utf-8", newline=""
        )
        return DashboardArtifact(path=path, session_count=len(sessions), sha256=sha256_file(path))

    @staticmethod
    def _session_payload(session: BenchmarkSession) -> dict[str, Any]:
        assistant = BenchmarkAssistant().explain(session)
        return {
            "id": session.session_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "backend": session.backend.get("name", session.configuration.backend.name),
            "device": session.configuration.backend.device,
            "hardware": session.hardware.summary(),
            "capabilities": session.hardware.capability_report(),
            "metrics": {
                metric.name: metric.value
                for metric in session.metrics
                if isinstance(metric.value, int | float)
            },
            "diagnostics": [
                diagnostic.model_dump(mode="json") for diagnostic in session.diagnostics
            ],
            "reports": [
                artifact.model_dump(mode="json")
                for artifact in session.artifacts
                if artifact.kind == "report"
            ],
            "assistant": {
                "summary": assistant.summary,
                "insights": [
                    {
                        "category": insight.category,
                        "summary": insight.summary,
                        "recommendation": insight.recommendation,
                        "confidence": insight.confidence,
                    }
                    for insight in assistant.insights
                ],
            },
        }


def _render_dashboard(title: str, payload: Mapping[str, object], available_sessions: int) -> str:
    """Render a CSP-protected shell; runtime data is consumed only as JSON text."""
    data = json.dumps(payload, sort_keys=True).replace("</", "<\\/")
    notice = ""
    if available_sessions >= DEFAULT_MAX_SESSIONS:
        notice = " Showing the most recent bounded history page."
    template = files("aihw_bench.presentation.assets").joinpath("dashboard.html")
    return (
        template.read_text(encoding="utf-8")
        .replace("__TITLE__", escape(title))
        .replace("__NOTICE__", notice)
        .replace("__DATA__", data)
    )

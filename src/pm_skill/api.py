from __future__ import annotations

from pathlib import Path
from typing import Any

from .command_router import command_specs, execute_command_envelope, supported_commands


class LocalRestApp:
    def __init__(self, project_path: str | Path = ".") -> None:
        self.project_path = project_path
        self.routes = ["/v1/commands", "/v1/command"]

    def handle(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if method.upper() == "GET" and path == "/v1/commands":
            return {"ok": True, "commands": supported_commands(), "specs": command_specs()}
        if method.upper() == "POST" and path == "/v1/command":
            return execute_command_envelope(self.project_path, payload or {})
        raise RuntimeError(f"Unsupported local REST route: {method} {path}")


def create_app(project_path: str | Path = ".") -> Any:
    try:
        from fastapi import FastAPI, HTTPException
    except Exception as exc:  # pragma: no cover - depends on optional future extra.
        return LocalRestApp(project_path)

    app = FastAPI(title="pm-skill", version="0.1.0")

    @app.get("/v1/commands")
    def list_commands() -> dict[str, Any]:
        return {"ok": True, "commands": supported_commands(), "specs": command_specs()}

    @app.post("/v1/command")
    def run_command(envelope: dict[str, Any]) -> dict[str, Any]:
        try:
            return execute_command_envelope(project_path, envelope)
        except Exception as exc:  # noqa: BLE001 - HTTP boundary.
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app

app = create_app()

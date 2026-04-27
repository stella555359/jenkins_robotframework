from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from .models import ResolvedConfig, TestlineContext
from .ue_extractor import UeExtractor


class EnvConfigResolver:
    def __init__(self, repository_root: Path | None = None):
        self.repository_root = repository_root or Path(__file__).resolve().parents[1]

    def env_map_path(self) -> Path:
        return self.repository_root / "configs" / "env_map.json"

    def load_env_map(self) -> dict[str, dict]:
        env_map_path = self.env_map_path()
        if not env_map_path.exists():
            raise FileNotFoundError(f"env_map.json not found: {env_map_path}")
        return json.loads(env_map_path.read_text(encoding="utf-8"))

    def resolve_env(self, env: str) -> ResolvedConfig:
        cleaned_env = str(env or "").strip().upper()
        if not cleaned_env:
            raise ValueError("env is required.")

        env_map = self.load_env_map()
        if cleaned_env not in env_map:
            raise ValueError(f"env is not defined in env_map.json: {cleaned_env}")

        entry = env_map[cleaned_env]
        config_path = self.repository_root / Path(str(entry["config_path"]))
        if not config_path.exists():
            raise FileNotFoundError(f"testline configuration file not found for {cleaned_env}: {config_path}")
        return ResolvedConfig(
            env=cleaned_env,
            config_id=str(entry["config_id"]),
            config_path=config_path,
            department=entry.get("department"),
            site=entry.get("site"),
            topology_id=entry.get("topology_id"),
            match_type=str(entry.get("match_type") or "static_map"),
            confidence=str(entry.get("confidence") or "high"),
            allowed_script_roots=list(entry.get("allowed_script_roots") or []),
        )

    def load_tl_module(self, env: str):
        resolved = self.resolve_env(env)
        module_name = f"gnb_kpi_tl_{resolved.config_id.lower()}"
        spec = importlib.util.spec_from_file_location(module_name, resolved.config_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to create module spec for testline config: {resolved.config_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def load_testline_context(self, env: str) -> TestlineContext:
        resolved = self.resolve_env(env)
        module = self.load_tl_module(env)
        tl = getattr(module, "tl", None)
        if tl is None:
            raise ValueError(f"Testline config does not define tl: {resolved.config_path}")

        extractor = UeExtractor()
        return TestlineContext(
            env=resolved.env,
            resolved_config=resolved,
            tl=tl,
            ues=extractor.extract(tl),
            gnbs=list(getattr(tl, "gnbs", []) or []),
            enbs=list(getattr(tl, "enbs", []) or []),
            appserver=getattr(tl, "appserver", None),
            test_pc=getattr(tl, "test_pc", None),
            raw_summary=extractor.extract_summary(tl),
        )

    def validate_script_path(self, env: str, script_path: str) -> None:
        resolved = self.resolve_env(env)
        normalized_script = str(script_path or "").replace("\\", "/").strip().lstrip("./")
        if not normalized_script:
            raise ValueError("script_path is required.")
        if Path(normalized_script).is_absolute():
            raise ValueError("script_path must be relative to an allowed script root.")
        if not any(
            normalized_script == root or normalized_script.startswith(f"{root}/")
            for root in resolved.allowed_script_roots
        ):
            allowed_text = ", ".join(resolved.allowed_script_roots) or "<empty>"
            raise ValueError(f"script_path must match allowed_script_roots for {env}: {allowed_text}")

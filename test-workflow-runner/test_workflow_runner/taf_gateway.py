from __future__ import annotations

import importlib
import os
from typing import Any


class TafGateway:
    def __init__(self, bindings_module: str | None = None):
        self.bindings_module = bindings_module or os.getenv("GNB_KPI_TAF_BINDINGS_MODULE", "").strip() or None
        self._module = None

    def _load_module(self):
        if self._module is not None:
            return self._module
        if not self.bindings_module:
            return None
        self._module = importlib.import_module(self.bindings_module)
        return self._module

    def execute(self, action: str, handler_context: Any) -> dict[str, Any]:
        module = self._load_module()
        if module is None:
            raise RuntimeError(
                f"No TAF bindings module configured for action '{action}'. "
                "Set runtime_options.bindings_module or GNB_KPI_TAF_BINDINGS_MODULE."
            )

        function_name = f"run_{action}"
        callback = getattr(module, function_name, None)
        if callback is None:
            raise RuntimeError(f"Bindings module '{self.bindings_module}' does not expose '{function_name}'.")

        result = callback(handler_context)
        if result is None:
            return {}
        if not isinstance(result, dict):
            raise RuntimeError(f"Binding '{function_name}' must return a dict, got: {type(result)!r}")
        return result

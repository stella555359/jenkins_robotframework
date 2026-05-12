from __future__ import annotations

import argparse
import os
from pathlib import Path


PLACEHOLDERS = {
    "__T813_AGENT_SSH_PRIVATE_KEY_BLOCK__": "T813_AGENT_SSH_PRIVATE_KEY_PATH",
    "__ROBOTWS_GIT_SSH_PRIVATE_KEY_BLOCK__": "ROBOTWS_GIT_SSH_PRIVATE_KEY_PATH",
    "__TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY_BLOCK__": "TESTLINE_CONFIGURATION_GIT_SSH_PRIVATE_KEY_PATH",
}


def _load_key_block(env_name: str) -> str:
    key_path = os.environ.get(env_name, "").strip()
    if not key_path:
        raise ValueError(f"Missing required environment variable: {env_name}")

    key_text = Path(key_path).read_text(encoding="utf-8").strip()
    if not key_text:
        raise ValueError(f"Key file is empty: {key_path}")

    indented_lines = [f"                    {line}" for line in key_text.splitlines()]
    return "|\n" + "\n".join(indented_lines)


def render_template(template_path: Path, output_path: Path) -> None:
    rendered = template_path.read_text(encoding="utf-8")

    for placeholder, env_name in PLACEHOLDERS.items():
        rendered = rendered.replace(placeholder, _load_key_block(env_name))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Jenkins JCasC YAML with SSH keys loaded from files.")
    parser.add_argument("--template", required=True, help="Path to the JCasC template file.")
    parser.add_argument("--output", required=True, help="Path to write the rendered JCasC file.")
    args = parser.parse_args()

    render_template(Path(args.template), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
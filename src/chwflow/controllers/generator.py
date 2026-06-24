"""GeneratorController — create parameterized workflow scripts from templates."""

from __future__ import annotations

import json
from pathlib import Path
from string import Template
from typing import Any


class GeneratorController:
    """Build parameterized workflow definitions programmatically.

    Can generate Python scripts, JSON configs, or shell scripts from
    predefined templates and user-provided values.
    """

    TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

    def __init__(self) -> None:
        self.generated: list[Path] = []

    def generate_json(
        self,
        name: str,
        goal: str,
        steps: list[dict[str, Any]],
        constraints: list[str] | None = None,
        out_path: str | None = None,
    ) -> dict[str, Any]:
        """Build a workflow JSON from parameters and optionally write to file."""
        workflow: dict[str, Any] = {
            "name": name,
            "goal": goal,
            "constraints": constraints or [],
            "steps": steps,
        }
        if out_path:
            p = Path(out_path)
            p.write_text(
                json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            self.generated.append(p)
        return workflow

    def generate_cli_script(
        self,
        script_name: str,
        description: str,
        commands: list[dict[str, Any]],
        out_path: str | None = None,
    ) -> str:
        """Generate a standalone Python CLI script with argparse subcommands."""
        subparser_lines = []
        for cmd in commands:
            cmd_name = cmd.get("name", "unknown")
            subparser_lines.append(
                f"    sub_{cmd_name} = sub.add_parser('{cmd_name}', help='{cmd.get('help', '')}')"
            )
            subparser_lines.append(f"    sub_{cmd_name}.set_defaults(func=cmd_{cmd_name})")
            subparser_lines.append("")

        script = f'''#!/usr/bin/env python3
"""{script_name}: {description}"""

import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")

{chr(10).join(subparser_lines)}
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
'''
        if out_path:
            p = Path(out_path)
            p.write_text(script, encoding="utf-8")
            p.chmod(0o755)
            self.generated.append(p)
        return script

    def from_template(
        self,
        template_name: str,
        variables: dict[str, str],
        out_path: str | None = None,
    ) -> str:
        """Render a template file with variable substitution."""
        tmpl_path = self.TEMPLATE_DIR / template_name
        if not tmpl_path.exists():
            raise FileNotFoundError(f"Template not found: {tmpl_path}")
        content = Template(tmpl_path.read_text(encoding="utf-8")).safe_substitute(**variables)
        if out_path:
            p = Path(out_path)
            p.write_text(content, encoding="utf-8")
            self.generated.append(p)
        return content

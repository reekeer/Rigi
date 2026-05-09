from __future__ import annotations

import argparse
from typing import Any

from rigi.commands.command import Command
from rigi.commands.registry import CommandRegistry


def _build_argparser_for_command(
    cmd: Command,
    parser: argparse.ArgumentParser,
) -> None:
    for arg in cmd.args:
        kwargs: dict[str, Any] = {"help": arg.help}
        if arg.is_flag:
            flags = [f"--{arg.name}"]
            if arg.short:
                flags.insert(0, f"-{arg.short}")
            kwargs["action"] = "store_true"
            kwargs["default"] = False
            parser.add_argument(*flags, **kwargs)
        else:
            flags = [f"--{arg.name}"]
            if arg.short:
                flags.insert(0, f"-{arg.short}")
            if arg.choices:
                kwargs["choices"] = arg.choices
            kwargs["type"] = arg.arg_type
            kwargs["default"] = arg.default
            if arg.required:
                kwargs["required"] = True
            parser.add_argument(*flags, **kwargs)

    if cmd.subcommands:
        subparsers = parser.add_subparsers(dest="_subcommand", title="subcommands")
        for sub in cmd.subcommands:
            if sub.hidden:
                continue
            sub_parser = subparsers.add_parser(
                sub.name,
                help=sub.help,
                aliases=sub.aliases,
            )
            _build_argparser_for_command(sub, sub_parser)


def build_cli_parser(
    prog_name: str,
    version: str,
    registry: CommandRegistry,
    description: str = "",
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog_name,
        description=description or f"{prog_name} v{version}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {version}",
    )

    subparsers = parser.add_subparsers(dest="_command", title="commands", metavar="<command>")

    for cmd in registry.visible():
        sub_parser = subparsers.add_parser(
            cmd.name,
            help=cmd.help,
            aliases=cmd.aliases,
        )
        _build_argparser_for_command(cmd, sub_parser)

    return parser


def parse_inline(text: str, registry: CommandRegistry) -> tuple[Command | None, dict[str, Any]]:
    parts = text.strip().split()
    if not parts:
        return None, {}

    cmd_name = parts[0]
    cmd = registry.get(cmd_name)
    if cmd is None:
        return None, {"_error": f"Unknown command: {cmd_name!r}"}

    rest = parts[1:]
    if rest and cmd.subcommands:
        sub = next(
            (s for s in cmd.subcommands if s.name == rest[0] or rest[0] in s.aliases),
            None,
        )
        if sub:
            cmd = sub
            rest = rest[1:]
        else:
            # Unknown subcommand — surface as error
            return None, {"_error": f"Unknown subcommand: {rest[0]!r} for {cmd.name!r}"}

    parsed: dict[str, Any] = {}
    i = 0
    while i < len(rest):
        token = rest[i]
        matched = False
        for arg in cmd.args:
            flags = {f"--{arg.name}"}
            if arg.short:
                flags.add(f"-{arg.short}")
            if token in flags:
                if arg.is_flag:
                    parsed[arg.name] = True
                else:
                    i += 1
                    if i < len(rest):
                        val = rest[i]
                        try:
                            parsed[arg.name] = arg.arg_type(val)
                        except (ValueError, TypeError):
                            parsed[arg.name] = val
                matched = True
                break
        if not matched:
            parsed.setdefault("_positional", []).append(token)
        i += 1

    for arg in cmd.args:
        if arg.name not in parsed:
            parsed[arg.name] = True if arg.is_flag else arg.default

    # Flatten positional tokens into numbered kwargs so handlers can use **kwargs
    for i2, val in enumerate(parsed.pop("_positional", [])):
        parsed[f"_arg{i2}"] = val

    return cmd, parsed

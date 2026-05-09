from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rigi.core.types import CommandArg, HandlerFn

if TYPE_CHECKING:
    pass


@dataclass
class Command:
    name: str
    help: str = ""
    args: list[CommandArg] = field(default_factory=list)
    handler: HandlerFn | None = None
    subcommands: list[Command] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    hidden: bool = False
    terminal_help: str = ""  # Подробная помощь для терминала
    subcommand_handlers: dict[str, HandlerFn] = field(default_factory=dict)  # Обработчики подкоманд

    def add_arg(
        self,
        name: str,
        help: str = "",
        required: bool = False,
        default: Any = None,
        arg_type: type[Any] = str,
        choices: list[str] | None = None,
        is_flag: bool = False,
        short: str | None = None,
    ) -> CommandArg:
        arg = CommandArg(
            name=name,
            help=help,
            required=required,
            default=default,
            arg_type=arg_type,
            choices=choices,
            is_flag=is_flag,
            short=short,
        )
        self.args.append(arg)
        return arg

    def add_subcommand(self, cmd: Command) -> Command:
        self.subcommands.append(cmd)
        return cmd

    def set_handler(self, fn: HandlerFn) -> Command:
        self.handler = fn
        return self

    def set_terminal_help(self, help_text: str) -> Command:
        """Устанавливает подробную помощь для терминала."""
        self.terminal_help = help_text
        return self

    def add_subcommand_handler(self, action: str, fn: HandlerFn) -> Command:
        """Добавляет обработчик для подкоманды (action)."""
        self.subcommand_handlers[action] = fn
        return self

    async def execute(self, parsed_args: dict[str, Any], app: object) -> None:
        # Проверяем наличие action для subcommand_handlers
        action = parsed_args.get("action")
        if action and action in self.subcommand_handlers:
            handler = self.subcommand_handlers[action]
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())
            kwargs: dict[str, Any] = {}
            if "app" in params:
                kwargs["app"] = app
            if "args" in params:
                kwargs["args"] = parsed_args
            for k, v in parsed_args.items():
                if k in params:
                    kwargs[k] = v
            result = handler(**kwargs)
            if asyncio.iscoroutine(result):
                await result
            return

        if self.handler is None:
            return
        sig = inspect.signature(self.handler)
        params = list(sig.parameters.keys())
        kwargs: dict[str, Any] = {}
        if "app" in params:
            kwargs["app"] = app
        if "args" in params:
            kwargs["args"] = parsed_args
        for k, v in parsed_args.items():
            if k in params:
                kwargs[k] = v
        result = self.handler(**kwargs)
        if asyncio.iscoroutine(result):
            await result

    def completion_hints(self, partial: str) -> list[str]:
        hints: list[str] = []
        for sub in self.subcommands:
            if sub.name.startswith(partial) and not sub.hidden:
                hints.append(sub.name)
            for alias in sub.aliases:
                if alias.startswith(partial):
                    hints.append(alias)
        for arg in self.args:
            flag = f"--{arg.name}"
            if flag.startswith(partial):
                hints.append(flag)
            if arg.short and f"-{arg.short}".startswith(partial):
                hints.append(f"-{arg.short}")
        return hints

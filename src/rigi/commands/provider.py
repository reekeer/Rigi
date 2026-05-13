"""Textual 8 CommandPalette provider for Rigi's command registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.command import Hit, Hits, Provider

from rigi.commands.command import Command

if TYPE_CHECKING:
    from rigi.core.app import App


def _fuzzy_score(query: str, candidate: str) -> float | None:
    """Return a normalised match score [0,1] or None if no match."""
    q = query.lower()
    c = candidate.lower()
    if not q:
        return 1.0
    pos = i = 0
    raw = 0
    while i < len(q) and pos < len(c):
        if q[i] == c[pos]:
            raw += 2 if (i > 0 and pos > 0 and q[i - 1] == c[pos - 1]) else 1
            if pos == 0:
                raw += 3
            i += 1
        pos += 1
    if i < len(q):
        return None
    return raw / max(len(candidate), 1)


class CommandProvider(Provider):
    """Bridges Rigi's CommandRegistry into Textual's built-in command palette."""

    _commands: list[Command]

    async def startup(self) -> None:
        app: App = self.app  # type: ignore[assignment]
        self._commands = list(app._cmd_registry.visible())

    async def search(self, query: str) -> Hits:
        def _run(name: str) -> None:
            app: App = self.app  # type: ignore[assignment]
            self.app.call_later(app._handle_command, name)

        scored: list[tuple[float, Command]] = []
        for cmd in self._commands:
            score = _fuzzy_score(query, cmd.name)
            if score is not None:
                scored.append((score, cmd))

        scored.sort(key=lambda x: -x[0])

        for score, cmd in scored:
            display = f"[bold]{cmd.name}[/bold]"
            if cmd.help:
                display += f"  [dim]{cmd.help}[/dim]"
            yield Hit(
                score=score,
                match_display=display,
                command=lambda n=cmd.name: _run(n),
                text=cmd.name,
                help=cmd.help or None,
            )

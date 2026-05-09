from __future__ import annotations

from rigi.commands.command import Command


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self._commands[alias] = cmd

    def get(self, name: str) -> Command | None:
        return self._commands.get(name)

    def all(self) -> list[Command]:
        seen: set[str] = set()
        result: list[Command] = []
        for name, cmd in self._commands.items():
            if cmd.name not in seen:
                seen.add(cmd.name)
                result.append(cmd)
        return result

    def visible(self) -> list[Command]:
        return [c for c in self.all() if not c.hidden]

    def completions(self, partial: str) -> list[str]:
        results: list[str] = []
        parts = partial.split()
        if len(parts) == 0 or (len(parts) == 1 and not partial.endswith(" ")):
            word = parts[0] if parts else ""
            # Prefix matches first
            prefix: list[str] = []
            fuzzy: list[tuple[int, str]] = []
            for cmd in self.visible():
                names = [cmd.name] + list(cmd.aliases)
                for n in names:
                    if n.startswith(word):
                        prefix.append(n)
                    elif word and self._fuzzy_match(word, n):
                        score = sum(1 for c in word if c in n)
                        fuzzy.append((-score, n))
            results = prefix + [n for _, n in sorted(fuzzy)]
        elif len(parts) >= 1:
            root = self.get(parts[0])
            if root:
                sub_partial = parts[-1] if not partial.endswith(" ") else ""
                results = root.completion_hints(sub_partial)
        return list(dict.fromkeys(results))  # deduplicate preserving order

    @staticmethod
    def _fuzzy_match(query: str, candidate: str) -> bool:
        q, c = query.lower(), candidate.lower()
        i = 0
        for ch in c:
            if i < len(q) and ch == q[i]:
                i += 1
        return i == len(q)

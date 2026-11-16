#!/usr/bin/env python3
"""Run a local Stanford GameMaster match between Python bots.

This runner expects rules mirrored by `stanford_gamemaster_fetch.py`.
Game logic is delegated to Stanford's downloaded `epilog.js` through the local
Node bridge in `stanford_gamemaster_engine.js`.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


ENGINE_SCRIPT = Path(__file__).with_name("stanford_gamemaster_engine.js")


class EngineError(RuntimeError):
    pass


class GamemasterEngine:
    def __init__(self, rules_path: Path, epilog_path: Path | None = None) -> None:
        cmd = ["node", str(ENGINE_SCRIPT), str(rules_path)]
        if epilog_path is not None:
            cmd.append(str(epilog_path))
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def close(self) -> None:
        if self._proc.poll() is None:
            try:
                self.request({"cmd": "quit"})
                self._proc.wait(timeout=1)
                return
            except Exception:
                pass
            try:
                self._proc.terminate()
                self._proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._proc.stdin is None or self._proc.stdout is None:
            raise EngineError("Engine process pipes are unavailable.")
        if self._proc.poll() is not None:
            stderr = ""
            if self._proc.stderr is not None:
                stderr = self._proc.stderr.read()
            raise EngineError(
                f"Engine process exited early with code {self._proc.returncode}.\n{stderr}"
            )
        self._proc.stdin.write(json.dumps(payload) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        if not line:
            stderr = ""
            if self._proc.stderr is not None:
                stderr = self._proc.stderr.read()
            raise EngineError(f"Engine produced no response.\n{stderr}")
        response = json.loads(line)
        if not response.get("ok", False):
            raise EngineError(str(response.get("error", "Unknown engine error")))
        return response

    def meta(self) -> dict[str, Any]:
        return self.request({"cmd": "meta"})

    def snapshot(self) -> dict[str, Any]:
        return self.request({"cmd": "snapshot", "include_legals": False})["snapshot"]

    def snapshot_with_legals(self) -> dict[str, Any]:
        return self.request({"cmd": "snapshot", "include_legals": True})["snapshot"]

    def apply(self, move: str) -> dict[str, Any]:
        return self.request({"cmd": "apply", "move": move})["snapshot"]


def load_module(module_path: Path) -> ModuleType:
    module_name = (
        "stanford_gamemaster_bot_"
        + hashlib.sha1(str(module_path.resolve()).encode("utf-8")).hexdigest()
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load bot module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bot(bot_path: Path) -> Callable[..., Any]:
    module = load_module(bot_path)
    fn = getattr(module, 'policy', None)
    if callable(fn):
        return fn
    raise RuntimeError(
        f"Bot {bot_path} must define policy"
    )


def call_bot(
    bot_fn: Callable[..., Any],
    state: list[Any],
    role: str,
    legal_moves: list[str],
) -> str:
    signature = inspect.signature(bot_fn)
    positional_params = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    has_varargs = any(
        parameter.kind == inspect.Parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )
    if len(positional_params) < 2 and not has_varargs:
        raise RuntimeError(
            f"{bot_fn.__name__} must accept positional arguments for state and role"
        )
    if len(positional_params) >= 3 or has_varargs:
        result = bot_fn(state, role, legal_moves)
    else:
        result = bot_fn(state, role)
    if result is None:
        raise RuntimeError(f"{bot_fn.__name__} returned None")
    return str(result).strip()


def bot_needs_legal_moves(bot_fn: Callable[..., Any]) -> bool:
    signature = inspect.signature(bot_fn)
    positional_params = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    has_varargs = any(
        parameter.kind == inspect.Parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )
    return len(positional_params) >= 3 or has_varargs


def resolve_default_epilog(rules_path: Path) -> Path:
    return rules_path.parent.parent / "assets" / "epilog.js"


def winner_from_scores(scores: dict[str, Any]) -> str | None:
    numeric_scores: dict[str, float] = {}
    for role, score in scores.items():
        try:
            numeric_scores[role] = float(score)
        except (TypeError, ValueError):
            return None
    if not numeric_scores:
        return None
    best_score = max(numeric_scores.values())
    winners = [role for role, score in numeric_scores.items() if score == best_score]
    if len(winners) == 1:
        return winners[0]
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=Path, required=True, help="Path to a .hrf rules file")
    parser.add_argument(
        "--bot-a",
        type=Path,
        required=True,
        help="Python bot script for the first role in the rulesheet",
    )
    parser.add_argument(
        "--bot-b",
        type=Path,
        help="Python bot script for the second role in the rulesheet",
    )
    parser.add_argument(
        "--epilog",
        type=Path,
        help="Optional explicit path to Stanford's downloaded epilog.js",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=512,
        help="Safety cap for turn count",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each turn as it is played",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rules_path = args.rules.resolve()
    epilog_path = args.epilog.resolve() if args.epilog else resolve_default_epilog(rules_path)

    if not rules_path.exists():
        raise RuntimeError(f"Rules file does not exist: {rules_path}")
    if not epilog_path.exists():
        raise RuntimeError(
            "Could not find epilog.js next to the mirrored rules. "
            f"Expected: {epilog_path}"
        )

    bot_a = load_bot(args.bot_a.resolve())
    bot_b_path = args.bot_b.resolve() if args.bot_b else args.bot_a.resolve()
    bot_b = load_bot(bot_b_path)

    engine = GamemasterEngine(rules_path=rules_path, epilog_path=epilog_path)
    try:
        roles = engine.meta()["roles"]
        if not roles:
            raise RuntimeError("No roles were found in the rulesheet.")
        if len(roles) > 2:
            raise RuntimeError(
                f"Only 1-role or 2-role games are supported by this runner. Found: {roles}"
            )
        if len(roles) == 1:
            raise RuntimeError(
                f"1-role games are not supported by this runner. Found: {roles}"
            )

        role_to_bot = {roles[0]: bot_a}
        role_to_label = {roles[0]: str(args.bot_a.resolve())}
        role_needs_legals = {roles[0]: bot_needs_legal_moves(bot_a)}
        if len(roles) == 2:
            role_to_bot[roles[1]] = bot_b
            role_to_label[roles[1]] = str(bot_b_path)
            role_needs_legals[roles[1]] = bot_needs_legal_moves(bot_b)

        history: list[str] = []
        turn_index = 0
        final_snapshot = engine.snapshot()

        while turn_index < args.max_turns:
            snapshot = engine.snapshot()
            final_snapshot = snapshot
            if snapshot["terminal"]:
                break

            control_role = snapshot["control"]
            if control_role is None:
                raise RuntimeError(
                    "This rulesheet does not expose a single `control(...)` role. "
                    "The current runner only supports turn-based GameMaster games."
                )
            if control_role not in role_to_bot:
                raise RuntimeError(f"Unexpected control role: {control_role}")

            if role_needs_legals.get(control_role, False):
                snapshot = engine.snapshot_with_legals()
                final_snapshot = snapshot

            legal_moves = snapshot["legal_moves"] or []
            if role_needs_legals.get(control_role, False) and not legal_moves:
                raise RuntimeError(
                    f"Role {control_role} is in control but there are no legal moves."
                )

            move = call_bot(
                role_to_bot[control_role],
                snapshot["state"],
                control_role,
                legal_moves,
            )
            if role_needs_legals.get(control_role, False) and move not in legal_moves:
                raise RuntimeError(
                    f"Bot for role {control_role} returned illegal move {move!r}. "
                    f"Legal moves: {legal_moves}"
                )

            if args.verbose:
                print(f"turn={turn_index} role={control_role} move={move}")

            engine.apply(move)
            history.append(move)
            turn_index += 1
        else:
            raise RuntimeError(f"Turn limit exceeded: {args.max_turns}")

        winner = winner_from_scores(final_snapshot["scores"])
        summary = {
            "rules_path": str(rules_path),
            "roles": roles,
            "bots": role_to_label,
            "turns": len(history),
            "history": history,
            "scores": final_snapshot["scores"],
            "winner": winner,
            "terminal": final_snapshot["terminal"],
        }
        print(json.dumps(summary, indent=2))
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)

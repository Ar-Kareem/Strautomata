import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from game_arena.base import Game
from game_arena.prompt_render import render_prompt, render_prompt_for_live_play
from game_arena.utils import get_config_file
from game_arena.stanford_gamemaster.stanford_gamemaster_generate_prompt import (
    choose_example_actions,
    format_prompt,
    load_game_info,
    sample_trajectory,
)
from game_arena.stanford_gamemaster.stanford_gamemaster_match import (
    EngineError,
    GamemasterEngine,
    resolve_default_epilog,
    winner_from_scores,
)


MODULE_DIR = Path(__file__).resolve().parent
SRC_DIR = MODULE_DIR.parent.parent


def _resolve_config_path(raw_path: str | Path) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate.resolve()
    search_roots = [
        Path.cwd(),
        MODULE_DIR,
        SRC_DIR,
    ]
    for root in search_roots:
        resolved = (root / candidate).resolve()
        if resolved.exists():
            return resolved
    return (MODULE_DIR / candidate).resolve()


def _resolve_rules_path(config: dict[str, Any]) -> Path:
    if "rules" in config:
        return _resolve_config_path(str(config["rules"]))
    game_name = config.get("game")
    if not game_name:
        raise RuntimeError(
            "StanfordGameMasterGame requires either config['game'] or config['rules']."
        )
    return (MODULE_DIR / "offline_mirror" / "rules" / f"{game_name}.hrf").resolve()


def _resolve_epilog_path(config: dict[str, Any], rules_path: Path) -> Path:
    if "epilog" in config:
        return _resolve_config_path(str(config["epilog"]))
    return resolve_default_epilog(rules_path)


def _term_to_action_text(value: Any) -> str:
    if isinstance(value, StanfordGameMasterMove):
        return value.text
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Move string is empty.")
        return text
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError("Move term cannot be empty.")
        functor = _term_to_action_text(value[0])
        if len(value) == 1:
            return functor
        args = ",".join(_term_to_action_text(item) for item in value[1:])
        return f"{functor}({args})"
    raise ValueError(f"Unsupported move value: {value!r}")


def _deepcopy_snapshot_value(value: Any) -> Any:
    return copy.deepcopy(value)


@dataclass(frozen=True)
class StanfordGameMasterMove:
    text: str

    def get_unparsed_str(self) -> str:
        return self.text


class StanfordGameMasterGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.rules_path = _resolve_rules_path(self.config)
        self.epilog_path = _resolve_epilog_path(self.config, self.rules_path)
        if not self.rules_path.exists():
            raise RuntimeError(f"Rules file does not exist: {self.rules_path}")
        if not self.epilog_path.exists():
            raise RuntimeError(f"epilog.js does not exist: {self.epilog_path}")

        self._engine = GamemasterEngine(
            rules_path=self.rules_path,
            epilog_path=self.epilog_path,
        )
        meta = self._engine.meta()
        self.roles: list[str] = list(meta["roles"])
        if not self.roles:
            self.close()
            raise RuntimeError("No roles were found in the rulesheet.")
        self.role_to_index = {role: idx for idx, role in enumerate(self.roles)}
        self.game_name = str(self.config.get("game", self.rules_path.stem))
        self._snapshot: dict[str, Any] = {}
        self._legal_moves_cache: Optional[list[str]] = None
        self._refresh_snapshot(include_legals=False)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        engine = getattr(self, "_engine", None)
        if engine is not None:
            engine.close()
            self._engine = None  # type: ignore[assignment]

    def _store_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._snapshot = snapshot
        self._legal_moves_cache = (
            list(snapshot["legal_moves"]) if snapshot.get("legal_moves") is not None else None
        )
        self._state = _deepcopy_snapshot_value(snapshot["state"])

    def _refresh_snapshot(self, include_legals: bool) -> dict[str, Any]:
        if getattr(self, "_engine", None) is None:
            raise RuntimeError("Game engine is closed.")
        snapshot = (
            self._engine.snapshot_with_legals()
            if include_legals
            else self._engine.snapshot()
        )
        self._store_snapshot(snapshot)
        return snapshot

    def _current_role(self) -> Optional[str]:
        return self._snapshot.get("control")

    def get_state(self) -> dict[str, Any]:
        return {
            "game": self.game_name,
            "done": bool(self._snapshot["terminal"]),
            "roles": list(self.roles),
            "role": self._current_role(),
            "state": _deepcopy_snapshot_value(self._snapshot["state"]),
            "scores": _deepcopy_snapshot_value(self._snapshot["scores"]),
            "terminal": bool(self._snapshot["terminal"]),
            "move_count": len(self._snapshot["move_history"]),
            "move_history": list(self._snapshot["move_history"]),
            "rules_path": str(self.rules_path),
        }

    def get_observation(self) -> dict[str, Any]:
        return {
            "state": _deepcopy_snapshot_value(self._snapshot["state"]),
            "role": self._current_role(),
        }

    def get_fixed_observation(self) -> dict[str, Any]:
        return self.get_state()

    def get_move(self, move_str: Any) -> StanfordGameMasterMove:
        return StanfordGameMasterMove(_term_to_action_text(move_str))

    def get_legal_moves(self) -> list[str]:
        if self.is_done():
            return []
        if self._legal_moves_cache is None:
            self._refresh_snapshot(include_legals=True)
        return list(self._legal_moves_cache or [])

    def game_step(self, move: StanfordGameMasterMove) -> None:
        if self.is_done():
            raise ValueError("Game is already finished")
        if getattr(self, "_engine", None) is None:
            raise RuntimeError("Game engine is closed.")
        try:
            snapshot = self._engine.apply(move.text)
        except EngineError as error:
            raise ValueError(str(error)) from error
        self._store_snapshot(snapshot)

    def current_player(self) -> int:
        role = self._current_role()
        if role is None:
            if self.is_done():
                return 0
            raise RuntimeError(
                "This Stanford rulesheet does not expose a single control(...) role."
            )
        return self.role_to_index[role]

    def is_done(self) -> bool:
        return bool(self._snapshot.get("terminal", False))

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.get_legal_moves()

    def live_play_observation(self) -> dict[str, Any]:
        return self.get_fixed_observation()

    def live_play_legal_moves(self) -> list[str]:
        return self.get_legal_moves()

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "move_count": len(self._snapshot["move_history"])}

        winner_role = winner_from_scores(self._snapshot["scores"])
        winner = self.role_to_index[winner_role] if winner_role is not None else None
        return {
            "done": True,
            "winner": winner,
            "move_count": len(self._snapshot["move_history"]),
            "scores": _deepcopy_snapshot_value(self._snapshot["scores"]),
            "roles": list(self.roles),
            "move_history": list(self._snapshot["move_history"]),
            "rules_path": str(self.rules_path),
        }

    @staticmethod
    def _build_detailed_prompt(config: dict[str, Any]) -> tuple[str, str]:
        rules_path = _resolve_rules_path(config)
        epilog_path = _resolve_epilog_path(config, rules_path)
        engine = GamemasterEngine(rules_path=rules_path, epilog_path=epilog_path)
        try:
            roles = engine.meta()["roles"]
            game_info = load_game_info(rules_path, roles)
            max_turns = int(config.get("max_prompt_turns", 512))
            decision_points, final_snapshot = sample_trajectory(engine, max_turns=max_turns)
            example_actions = choose_example_actions(engine, decision_points)
            detailed_prompt = format_prompt(
                game_info,
                decision_points,
                final_snapshot,
                example_actions=example_actions,
            )
            sample_action = (
                example_actions.get(0)
                if decision_points and 0 in example_actions
                else (
                    decision_points[0].applied_action
                    if decision_points
                    else "action_name(arg1,arg2)"
                )
            )
            return detailed_prompt, sample_action
        finally:
            engine.close()

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        detailed_prompt, sample_action = StanfordGameMasterGame._build_detailed_prompt(config)
        game_name = config.get("game", _resolve_rules_path(config).stem)
        state_lines = [
            "`state` is the raw Stanford GameMaster list of currently true propositions.",
            "Each proposition is a term-like Python list, for example `[\"cell\", \"1\", \"1\", \"white\"]`.",
            "`role` is the role whose move your policy must choose in the current state.",
            "You are not given the legal-action list during normal play.",
        ]
        action_lines = [
            "Return exactly one legal action string in Stanford syntax.",
            f"Example action syntax: `{sample_action}`.",
            "If the state contains a control fact, your returned action must be legal for that role.",
        ]
        if live_play:
            base_prompt = render_prompt_for_live_play(
                game_name=f'Stanford GameMaster game "{game_name}"',
                state=state_lines,
                action=action_lines,
                example_action=json.dumps(sample_action),
            )
        else:
            base_prompt = render_prompt(
                role=[
                    "You are an AI competing in a gaming arena."
                ],
                objective=[
                    f'Write a complete Python file that provides the next move for a Stanford GameMaster game "{game_name}".',
                    "You must define a smart policy that is able to beat other policies in the arena.",
                    "You will be disqualified if you do not return a legal move string. Therefore, you must always return a legal move string.",
                ],
                signature_block="The provided python file must implement the following API:\n" + (
                    "```python\n"
                    "def policy(state: list[list[object]], role: str) -> str:\n"
                    "    ...\n"
                    "```"
                ),
                state=state_lines,
                action=action_lines,
                constraints=[
                    "You may use any standard Python imports, including numpy.",
                    "Your code is allowed 1 second of execution time on a modern 3GHz CPU.",
                ],
                output_format=[
                    "Output your strategy before providing the Python source code for your policy.",
                    "Output the Python source code for your policy surrounded by `<code>...</code>` tags.",
                ],
                example_output=(
                    "The strategy for this policy is...\n"
                    "<code>\n"
                    "...\n"
                    "</code>"
                ),
            )
        if live_play:
            return base_prompt.rstrip() + "\n\n# Detailed Game Reference\n\n" + detailed_prompt

        sections = base_prompt.rstrip().split("\n\n# Constraints\n\n", 1)
        if len(sections) != 2:
            raise RuntimeError("Unexpected prompt layout while reordering Stanford prompt sections.")
        body_before_constraints, trailing_sections = sections
        return (
            body_before_constraints
            + "\n\n# Detailed Game Reference\n\n"
            + detailed_prompt
            + "\n\n# Constraints\n\n"
            + trailing_sections
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", default="w_pentago")
    parser.add_argument("--live-play", action="store_true")
    args = parser.parse_args()

    config = get_config_file("stanford_gamemaster", args.world)
    prompt = StanfordGameMasterGame.get_prompt(config=config, live_play=args.live_play)
    print(prompt)
    # output_name = "prompt_example_live_play.txt" if args.live_play else "prompt_example.txt"
    output_name = args.world + "_prompt_example" + ("_live_play.txt" if args.live_play else ".txt")
    (Path(__file__).parent / 'prompts' / output_name).write_text(prompt)

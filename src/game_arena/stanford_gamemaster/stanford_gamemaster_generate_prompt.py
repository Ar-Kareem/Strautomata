#!/usr/bin/env python3
"""Generate a human-facing policy prompt for a Stanford GameMaster game."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .stanford_gamemaster_match import GamemasterEngine, resolve_default_epilog


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MIRROR = SCRIPT_DIR / "offline_mirror"
DEFAULT_SECTION_SIZE = 4


@dataclass
class GameInfo:
    game: str
    roles: list[str]
    description: str | None
    rulesheet: str


@dataclass
class DecisionPoint:
    turn_index: int
    control_role: str | None
    state: list[object]
    applied_action: str


def load_manifest(mirror_root: Path) -> list[dict[str, object]]:
    manifest_path = mirror_root / "manifest.json"
    if not manifest_path.exists():
        return []
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def extract_textarea(html_text: str, label: str) -> str | None:
    pattern = re.compile(
        rf"<td[^>]*>\s*{re.escape(label)}\s*</td>\s*<td[^>]*>\s*<textarea[^>]*>(.*?)</textarea>",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html_text)
    if not match:
        return None
    return html.unescape(match.group(1)).strip()


def load_game_info(rules_path: Path, roles: list[str]) -> GameInfo:
    mirror_root = rules_path.parent.parent
    try:
        relative_rules_path = rules_path.relative_to(mirror_root).as_posix()
    except ValueError:
        relative_rules_path = rules_path.name
    manifest = load_manifest(mirror_root)
    entry = next(
        (
            candidate
            for candidate in manifest
            if candidate.get("rules_path") == relative_rules_path
        ),
        None,
    )

    game = rules_path.stem
    description: str | None = None
    rulesheet = rules_path.read_text(encoding="utf-8").strip()

    if entry is not None:
        game = str(entry.get("game", game))
        info_path_text = entry.get("info_path")
        if isinstance(info_path_text, str):
            info_path = mirror_root / info_path_text
            if info_path.exists():
                info_html = info_path.read_text(encoding="utf-8")
                description = extract_textarea(info_html, "Description")
                rulesheet_text = extract_textarea(info_html, "Rulesheet")
                if rulesheet_text:
                    rulesheet = rulesheet_text

    if description is not None and not description.strip():
        description = None

    return GameInfo(game=game, roles=roles, description=description, rulesheet=rulesheet)


def sample_trajectory(engine: GamemasterEngine, max_turns: int) -> tuple[list[DecisionPoint], dict[str, object]]:
    decision_points: list[DecisionPoint] = []
    final_snapshot = engine.snapshot()

    for turn_index in range(max_turns):
        snapshot = engine.snapshot()
        final_snapshot = snapshot
        if snapshot["terminal"]:
            return decision_points, final_snapshot

        legal_reply = engine.request({"cmd": "legalx"})
        action = legal_reply.get("move")
        if not isinstance(action, str) or not action:
            raise RuntimeError(
                f"Could not find a legal action for turn {turn_index} in a non-terminal state."
            )

        decision_points.append(
            DecisionPoint(
                turn_index=turn_index,
                control_role=snapshot.get("control"),
                state=snapshot["state"],
                applied_action=action,
            )
        )
        final_snapshot = engine.apply(action)

    raise RuntimeError(f"Turn limit exceeded while sampling a trajectory: {max_turns}")


def quantile_index(total: int, fraction: float) -> int:
    if total <= 1:
        return 0
    return round((total - 1) * fraction)


def padded_range(start: int, end: int, count: int, total: int) -> list[int]:
    if total <= 0:
        return []
    start = max(0, min(start, total - 1))
    end = max(0, min(end, total - 1))
    if end < start:
        end = start
    if count <= 1:
        return [start]
    if start == end:
        return [start] * count
    return [
        round(start + ((end - start) * idx) / (count - 1))
        for idx in range(count)
    ]


def one_based_positions_to_indices(positions: list[int], total: int) -> list[int]:
    if total <= 0:
        return []
    return [max(1, min(position, total)) - 1 for position in positions]


def phase_indices(total: int) -> list[tuple[str, list[int]]]:
    opening = one_based_positions_to_indices([1, 2, 3, 4], total)
    early = one_based_positions_to_indices([10, 11, 12, 13], total)
    late = one_based_positions_to_indices(
        [total - 13, total - 12, total - 11, total - 10],
        total,
    )
    ending = one_based_positions_to_indices(
        [total - 3, total - 2, total - 1, total],
        total,
    )
    return [
        ("First 4 State/Action Examples", opening),
        ("4 Early-Game State/Action Examples", early),
        ("4 Late-Game State/Action Examples", late),
        ("Last 4 State/Action Examples", ending),
    ]


def compact_state_text(state: list[object]) -> str:
    return json.dumps(state, ensure_ascii=True, separators=(", ", ": "))


def action_family(action: str) -> str:
    head, separator, _ = action.partition("(")
    if separator:
        return head
    return action


def ordered_example_indices(decision_points: list[DecisionPoint]) -> tuple[list[tuple[str, list[int]]], list[int]]:
    sections = phase_indices(len(decision_points))
    ordered_indices: list[int] = []
    seen_indices: set[int] = set()
    for _, indices in sections:
        for index in indices:
            if index in seen_indices:
                continue
            seen_indices.add(index)
            ordered_indices.append(index)
    return sections, ordered_indices


def choose_example_actions(
    engine: GamemasterEngine,
    decision_points: list[DecisionPoint],
) -> dict[int, str]:
    if not decision_points:
        return {}

    _, ordered_indices = ordered_example_indices(decision_points)
    target_indices = set(ordered_indices)
    legal_moves_by_index: dict[int, list[str]] = {}

    engine.request({"cmd": "reset"})
    try:
        for index, point in enumerate(decision_points):
            if index in target_indices:
                snapshot = engine.snapshot_with_legals()
                legal_moves = snapshot.get("legal_moves") or []
                legal_moves_by_index[index] = [
                    move
                    for move in legal_moves
                    if isinstance(move, str) and move.strip()
                ]
            engine.apply(point.applied_action)
    except Exception:
        engine.request({"cmd": "reset"})
        raise

    family_counts: dict[str, int] = {}
    chosen_actions: dict[int, str] = {}
    for index in ordered_indices:
        point = decision_points[index]
        legal_moves = legal_moves_by_index.get(index, [])
        if not legal_moves:
            chosen_action = point.applied_action
        else:
            representative_by_family: dict[str, str] = {}
            for move in legal_moves:
                representative_by_family.setdefault(action_family(move), move)
            applied_family = action_family(point.applied_action)
            chosen_family, chosen_action = min(
                representative_by_family.items(),
                key=lambda item: (
                    family_counts.get(item[0], 0),
                    0 if item[0] == applied_family else 1,
                    item[1],
                ),
            )
            family_counts[chosen_family] = family_counts.get(chosen_family, 0) + 1
            chosen_actions[index] = chosen_action
            continue

        chosen_family = action_family(chosen_action)
        family_counts[chosen_family] = family_counts.get(chosen_family, 0) + 1
        chosen_actions[index] = chosen_action

    engine.request({"cmd": "reset"})
    return chosen_actions


def format_examples(
    decision_points: list[DecisionPoint],
    example_actions: dict[int, str] | None = None,
) -> str:
    if not decision_points:
        return "No decision points were sampled because the game started in a terminal state."

    lines: list[str] = []
    sections, ordered_indices = ordered_example_indices(decision_points)
    all_indices = [index for _, indices in sections for index in indices]
    repeated_examples = len(set(all_indices)) != len(all_indices)
    action_lookup = example_actions or {
        index: decision_points[index].applied_action for index in ordered_indices
    }

    for title, indices in sections:
        lines.append(title)
        for example_number, index in enumerate(indices, start=1):
            point = decision_points[index]
            lines.append(f"{example_number}. Turn {point.turn_index}")
            lines.append(f"Role input: {point.control_role or 'unknown'}")
            lines.append(
                f"State ({len(point.state)} facts, exact runtime input): {compact_state_text(point.state)}"
            )
            lines.append(
                f"One legal action from this state: {action_lookup.get(index, point.applied_action)}"
            )
            lines.append("")

    if repeated_examples:
        lines.append(
            "Note: this game has fewer than 16 distinct sampled decision points, so some examples repeat across sections."
        )

    return "\n".join(lines).rstrip()


def format_prompt(
    game_info: GameInfo,
    decision_points: list[DecisionPoint],
    final_snapshot: dict[str, object],
    example_actions: dict[int, str] | None = None,
) -> str:
    description = game_info.description or "No natural-language description was available in the mirrored Stanford page."
    roles_text = ", ".join(game_info.roles)
    ended_terminal = "yes" if final_snapshot.get("terminal") else "no"
    example_text = format_examples(decision_points, example_actions=example_actions)
    sample_fact = '["control", "role"]'
    sample_action = "action_name(arg1,arg2)"
    if decision_points:
        first_state = decision_points[0].state
        sample_action = (
            example_actions.get(0)
            if example_actions is not None and 0 in example_actions
            else decision_points[0].applied_action
        )
        for fact in first_state:
            if not (isinstance(fact, list) and len(fact) == 2 and fact[0] == "control"):
                sample_fact = json.dumps(fact, ensure_ascii=True)
                break
        else:
            if first_state:
                sample_fact = json.dumps(first_state[0], ensure_ascii=True)

    lines = [
        f'You are preparing to act as a player for the Stanford GameMaster game "{game_info.game}".',
        "",
        "Roles in the game",
        f"- All roles in the game: {roles_text}",
        "",
        "What you will receive at runtime",
        "- Inputs: `state`, `role`",
        "- `state` is the complete list of currently true Stanford propositions for the current position.",
        "- `role` is the role whose move you must choose for in the current position.",
        f"- Each proposition is encoded as a term-like JSON/Python list such as `{sample_fact}`.",
        "- If a proposition is absent from `state`, treat it as false.",
        '- In multi-player turn-based games, a fact such as `["control", "white"]` usually matches the current `role` input.',
        "",
        "What you must output",
        f"- Output exactly one legal action in Stanford syntax for the provided `role`, for example `{sample_action}`.",
        "- You will NOT be given the legal-action list at runtime.",
        "- You must infer legality and strategy from the state format, game description, and the examples below.",
        "- Optimize for winning and high final score.",
        "",
        "Game overview",
        f"- Description: {description}",
        "- The sampled states below come from one deterministic legal trajectory.",
        "- For each sampled state, the displayed action is one legal action from that state, chosen to expose action patterns that actually occur in the game.",
        "- The displayed actions are examples of legal moves, not guaranteed to be optimal moves or the exact moves used to generate later sampled states.",
        "- The policy should work for any role in the game, not just one fixed role.",
        "",
        "Representative state/action examples",
        example_text,
        "",
        "Sample trajectory summary",
        f"- Sampled decision points: {len(decision_points)}",
        f"- Sample ended in terminal state: {ended_terminal}",
        f'- Final scores in the sampled trajectory: {json.dumps(final_snapshot.get("scores", {}), ensure_ascii=True, sort_keys=True)}',
    ]
    return "\n".join(lines).strip() + "\n"

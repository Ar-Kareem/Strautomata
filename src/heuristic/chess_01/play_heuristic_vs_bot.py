import inspect
import json
import random
import sys
from pathlib import Path
from importlib import util

from IPython.display import clear_output

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT / "src"))

from src.game_arena import utils  # noqa: E402


def _load_heuristic_policy():
    heuristic_path = Path(__file__).resolve().parent / "heuristic.py"
    spec = util.spec_from_file_location("chess_heuristic", heuristic_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load heuristic from {heuristic_path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.policy


def _load_passthrough_policy():
    passthrough_path = Path(__file__).resolve().parent / "passthrough.py"
    spec = util.spec_from_file_location("chess_passthrough", passthrough_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load passthrough from {passthrough_path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.policy


def _select_opponent(bots, prefixes):
    results = []
    for name, policy in bots:
        if any(name.startswith(prefix) for prefix in prefixes):
            results.append((name, policy))
    if results:
        return random.choice(results)
    if bots:
        return bots[0]
    return "random_2", utils.get_the_random_policy()


def main():
    game_str = "chess"
    world = "world1"

    game = utils.get_game(game_name=game_str)
    ex = utils.get_examples_dir(game_str) / world
    config_path = ex / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}

    heuristic_policy = _load_heuristic_policy()
    bots = list(utils.get_bot_jsons(ex).items()) if ex.exists() else []
    opponent = _select_opponent(
        bots,
        prefixes=("gpt_5.2", "gemini_3_flash_preview", "minimax_m2"),
    )

    b1 = ("heuristic_1", heuristic_policy)
    b2 = opponent
    players = [b1, b2]
    print("playing against", opponent[0])

    game_inst = game(config)
    i = 0

    while not game_inst.is_done():
        kwargs = game_inst.get_observation()
        current_player = game_inst.current_player()
        name = players[current_player][0]
        policy = players[current_player][1]
        print("current_player", current_player, "name", name)
        print("kwargs", kwargs)
        print("legal_moves", sorted([m for m in game_inst.get_legal_moves()]))
        if hasattr(game_inst, "_state"):
            print(game_inst._state)
        if hasattr(game_inst, "visualize"):
            game_inst.visualize()
        assert current_player >= 0 and current_player < len(players), "Current player is out of range"
        if "_debug_legal_moves" in inspect.signature(policy).parameters:
            kwargs["_debug_legal_moves"] = game_inst.get_legal_moves()
        action_str = policy(**kwargs)  # type: ignore
        action_pre = None
        if isinstance(action_str, int):
            action_pre = action_str
            action_str = game_inst.action_to_human(action_str)
        if "input" in name:
            clear_output()
        action = game_inst.get_move(action_str)
        if action_pre is not None and action_pre != action.action:
            print("WARNING: action changed from", action_pre, "to", action)
        print(f"{name} chose {action_str} and applied {action}")
        game_inst.game_step(action)
        print("---")
        if game_inst.is_done():
            break
        kwargs = game_inst.get_observation()
        if hasattr(game_inst, "visualize"):
            game_inst.visualize()
        i += 1
    print("game over")
    stats = game_inst.get_final_stats()
    winner_idx = stats['winner']
    if winner_idx == 0:
        print("heuristic won")
    elif winner_idx == 1:
        print(f"{opponent[0]} won")
    else:
        print("winner =", winner_idx)
    print("stats", stats)
    return stats


if __name__ == "__main__":
    main()

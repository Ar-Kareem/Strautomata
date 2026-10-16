import json
import random
import sys
from importlib import util
from pathlib import Path

from IPython.display import clear_output


def _load_policy(path: Path, name: str):
    spec = util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load policy from {path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.policy


def main():
    REPO_ROOT = Path(__file__).resolve().parents[3]
    sys.path.append(str(REPO_ROOT / "src"))
    sys.path.append(str(REPO_ROOT))
    print('appending to path', REPO_ROOT / "src")

    from src.game_arena import utils  # noqa: E402

    game_str = "chess"
    world = "worlduci1"

    game = utils.get_game(game_name=game_str)
    ex = utils.get_examples_dir(game_str) / world
    config_path = ex / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}

    sunfish_path = Path(__file__).resolve().parent / "passthrough.py"
    sunfish_policy = _load_policy(sunfish_path, "sunfish_policy")
    
    bots = list(utils.get_bot_jsons(ex).items()) if ex.exists() else []
    # bots = [b for b in bots if b[0].startswith('claude_opus_4.6/005')]
    if not bots:
        raise RuntimeError(f"No bots found in {ex}")
    opponent = random.choice(bots)

    players = [
        ("sunfish_passthrough", sunfish_policy),
        opponent,
    ]
    print("playing against", opponent[0])

    game_inst = game(config)

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
        print('kwargs, keys', kwargs.keys())
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

    print("game over")
    stats = game_inst.get_final_stats()
    winner_idx = stats['winner']
    if winner_idx in [0, 1]:
        print(f"{players[winner_idx][0]} won")
    else:
        print("winner =", winner_idx)
    print("stats", stats)
    return stats


if __name__ == "__main__":
    main()

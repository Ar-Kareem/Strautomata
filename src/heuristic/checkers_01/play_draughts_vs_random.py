import json
import random
import sys
from importlib import util
from pathlib import Path

from IPython.display import clear_output

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT / "src"))
sys.path.append(str(REPO_ROOT))

from src.game_arena import utils  # noqa: E402


def _load_policy(path: Path, name: str):
    spec = util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load policy from {path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.policy


def _load_draughts_policy():
    passthrough_path = Path(__file__).resolve().parent / "passthrough.py"
    return _load_policy(passthrough_path, "draughts_policy")


def main():
    game_str = "checkers"
    world = "world1"

    game = utils.get_game(game_name=game_str)
    ex = utils.get_examples_dir(game_str) / world
    config_path = ex / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}

    draughts_policy = _load_draughts_policy()

    bots = list(utils.get_bot_jsons(ex).items()) if ex.exists() else []
    random_bot = ('random', utils.get_the_random_policy())
    if not bots:
        raise RuntimeError(f"No bots found in {ex}")
    filter_name = None
    # filter_name = 'gpt_5_mini/004'
    # filter_name = 'gemini_3_flash_preview/004'
    # filter_name = 'gemini_3_pro_preview/005'
    filter_name = 'glm_5/004'
    if filter_name:
        bots = [b for b in bots if b[0] == filter_name]
    opponent = random.choice(bots)
    # opponent = random_bot

    players = [
        opponent,
        ("draughts_passthrough", draughts_policy),
    ]
    print("playing against", opponent[0])

    game_inst = game(config)
    move_history = []
    previous_name = None
    while not game_inst.is_done():
        kwargs = game_inst.get_observation()
        current_player = game_inst.current_player()
        name = players[current_player][0]
        policy = players[current_player][1]
        print("current_player", current_player, "name", name, 'Turn', game_inst.turn)
        print("move_history", move_history)
        print("kwargs", kwargs)
        print("legal_moves", sorted([m for m in game_inst.get_legal_moves()]))
        double_jump = False
        for m in game_inst.get_legal_moves():
            from_file, from_rank, to_file, to_rank = m
            from_rank = int(from_rank)
            to_rank = int(to_rank)
            from_file = ord(from_file) - ord('a')
            to_file = ord(to_file) - ord('a')
            if from_file == to_file and abs(from_rank - to_rank) == 2:
                double_jump = True
                break
            
        if hasattr(game_inst, "_state"):
            print(game_inst._state)
        if hasattr(game_inst, "visualize"):
            game_inst.visualize()
        print(name)
        assert current_player >= 0 and current_player < len(players), "Current player is out of range"
        action_str = policy(**kwargs)  # type: ignore
        action_pre = None
        if isinstance(action_str, int):
            action_pre = action_str
            action_str = game_inst.action_to_human(action_str)
        if "input" in name:
            clear_output()
        action = game_inst.get_move(action_str)
        move_history.append((current_player, action.action_str))
        if action_pre is not None and action_pre != action.action:
            print("WARNING: action changed from", action_pre, "to", action)
        print(f"{name} chose {action_str} and applied {action}")
        game_inst.game_step(action)
        if hasattr(game_inst, "visualize"):
            game_inst.visualize()
        print("---")
        if double_jump:
            print("double jump")
            input()
        if previous_name == name:
            print("same player")
            # input()
        # input()
        previous_name = name


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

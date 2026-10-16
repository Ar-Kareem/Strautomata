import argparse
import inspect
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT / "src"))

from game_arena import utils  # noqa: E402
from game_arena.chess.game import ChessGame  # noqa: E402
from heuristic.chess_lc0_0_20 import passthrough as lc0  # noqa: E402


def _format_dt(seconds: float) -> str:
    if seconds >= 1.0:
        return f"{seconds:.2f}s"
    if seconds >= 0.001:
        return f"{seconds * 1000:.2f}ms"
    return f"{seconds * 1_000_000:.0f}us"


def _resolve_bot(bot: str, world: str) -> tuple[str, Path | None]:
    bot_paths = utils.get_bot_paths_from_world("chess", world, add_random=True)
    if bot in bot_paths:
        return bot, bot_paths[bot]

    path = Path(bot)
    if path.exists():
        label = path.stem if path.is_file() else path.name
        return label, path

    sample = ", ".join(sorted(bot_paths)[:20])
    raise SystemExit(f"Unknown bot {bot!r}. Example available bots in {world}: {sample}")


def _print_lc0_debug(info: dict) -> None:
    timings = info.get("timings", [])
    if not timings:
        return
    non_aggregate = [
        (label, dt)
        for label, dt in timings
        if not (label.endswith(".total") or label.endswith("_total"))
    ]
    slowest_label, slowest_dt = max(non_aggregate or timings, key=lambda item: item[1])
    max_label_len = max(len(label) for label, _ in timings)
    print(f"    fen: {info.get('fen', '')}")
    print(f"    slowest: {slowest_label} ({_format_dt(slowest_dt)})")
    for label, dt in timings:
        marker = " <==" if label == slowest_label and dt == slowest_dt else ""
        print(f"    {label:<{max_label_len}}  {_format_dt(dt):>8}{marker}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", required=True, help="Bot name in the selected world, or a local file/dir path.")
    parser.add_argument("--world", default="worlduci1")
    parser.add_argument(
        "--lc0-side",
        choices=("white", "black"),
        default="white",
        help="Which side lc0 should play. In this arena, white moves first.",
    )
    parser.add_argument(
        "--moves",
        type=int,
        default=20,
        help="Maximum number of plies (half-moves) to play before stopping.",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--move-time-ms", type=int, default=lc0.DEFAULT_MOVE_TIME_MS)
    parser.add_argument("--debug", action="store_true", help="Print per-step lc0 timing breakdown each move.")
    args = parser.parse_args()

    if args.seed is not None:
        utils.set_seed(args.seed)

    bot_name, bot_path = _resolve_bot(args.bot, args.world)
    opponent = utils.get_policy_fn_with_memory(bot_name, bot_path)
    config = utils.get_config_file("chess", args.world)
    game = ChessGame(config)

    if args.lc0_side == "white":
        players = [opponent, ("lc0 20", None)]
    else:
        players = [("lc0 20", None), opponent]

    lc0_memory: dict = {}

    print(
        f"lc0 20 vs {bot_name} | side={args.lc0_side} | world={args.world} "
        f"| seed={args.seed} | max_plies={args.moves} | move_time_ms={args.move_time_ms}"
    )

    for ply in range(args.moves):
        if game.is_done():
            break
        obs = game.get_observation()
        current_player = game.current_player()
        name, policy = players[current_player]
        started_at = time.perf_counter()
        debug_info = None

        try:
            if name == "lc0 20":
                move, lc0_memory, debug_info = lc0.choose_move(
                    obs["pieces"],
                    to_play=obs["to_play"],
                    move_time_ms=args.move_time_ms,
                    memory=lc0_memory,
                    debug=args.debug,
                )
            else:
                assert policy is not None
                opponent_kwargs = dict(obs)
                param_names = set(inspect.signature(policy).parameters)
                if "legal_moves" in param_names:
                    opponent_kwargs["legal_moves"] = game.get_legal_moves()
                if "_debug_legal_moves" in param_names:
                    opponent_kwargs["_debug_legal_moves"] = game.get_legal_moves()
                move = policy(**opponent_kwargs)  # type: ignore[arg-type]
            elapsed = time.perf_counter() - started_at
            print(f"ply {ply + 1:>3} | {obs['to_play']:<5} | {name:<24} | {move:<6} | {_format_dt(elapsed)}")
            if args.debug and name == "lc0 20" and debug_info is not None:
                _print_lc0_debug(debug_info)
            action = game.get_move(move)
            game.game_step(action)
        except Exception as exc:
            elapsed = time.perf_counter() - started_at
            print(f"ply {ply + 1:>3} | {obs['to_play']:<5} | {name:<24} | ERROR  | {_format_dt(elapsed)}")
            print(f"    {type(exc).__name__}: {exc}")
            print(f"    legal_moves: {game.get_legal_moves()}")
            break

    print("final_stats", game.get_final_stats())


if __name__ == "__main__":
    main()

"""Verify that the repo is installed correctly and every game runs end to end.

Checks, in order:
  1. Python version and the packages in requirements.txt (plus optional extras).
  2. Repo layout and that the core game_arena / experimental modules import.
  3. For every main game: the engine loads, a random game finishes, and a few
     real matches are played through the same process-isolated runner used by
     quals and the tournament (random vs random, automaton vs random, a quals
     style pair from one model, and a tournament style pair across models).
  4. The rating code (BT ELO and quals CI rankings) runs on the played matches.

Usage (from the repo root or anywhere):
    python scripts/verify_installation.py
    python scripts/verify_installation.py --games chess,go --timeout 2
    python scripts/verify_installation.py --skip-matches
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import os
import random
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
CODE_FILE = '2.python_code.py'

# Per-automaton tournament ELOs. Used to sample working automata (many weak ones crash by design).
ELO_CSV = SRC / 'frontend' / 'arena_fe' / 'public' / 'elos_all_bots.csv'
# Fallback if experimental.exp_utils cannot be imported (that failure is reported separately).
FALLBACK_GAMES = [
    ('tic_tac_toe_3d', 'world1', '3D TTT'), ('tic_tac_toe', 'world1', '3x3 TTT'), ('tic_tac_toe', 'world2', '4x4 TTT'),
    ('battleships', 'world1', 'Battleships'), ('connect4', 'world1', 'Connect4'), ('lines_of_action', 'world1', 'LoA'),
    ('mancala', 'world1', 'Mancala'), ('clobber', 'world1', 'Clobber'), ('pentago', 'world1', 'Pentago'),
    ('amazons', 'world1', 'Amazons'), ('backgammon', 'world1', 'Backgammon'), ('nim', 'world1', 'Nim'),
    ('othello', 'world1', 'Othello'), ('dots_and_boxes', 'world1', 'Dots&B'), ('breakthrough', 'world1', 'Breakthrough'),
    ('hex', 'world1', 'Hex'), ('havannah', 'world1', 'Havannah'), ('go', 'world1', 'Go'),
    ('checkers', 'world1', 'Checkers'), ('chess', 'worlduci1', 'Chess UCI'),
]
IMPORT_NAMES = {'open_spiel': 'pyspiel', 'pillow': 'PIL'}
OPTIONAL_PACKAGES = {
    'requests': 'needed only for prompting new automata (game_arena.prompter)',
    'dotenv': 'needed only for prompting new automata (python-dotenv)',
}

GREEN, RED, YELLOW, DIM, RESET = '\033[32m', '\033[31m', '\033[33m', '\033[2m', '\033[0m'
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ''


class Report:
    def __init__(self):
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def ok(self, msg: str):
        print(f'  {GREEN}OK{RESET}    {msg}')

    def warn(self, msg: str):
        self.warnings.append(msg)
        print(f'  {YELLOW}WARN{RESET}  {msg}')

    def fail(self, msg: str, detail: str | None = None):
        self.failures.append(msg)
        print(f'  {RED}FAIL{RESET}  {msg}')
        if detail:
            print(DIM + '\n'.join('        ' + line for line in detail.rstrip().splitlines()[-15:]) + RESET)


def section(title: str):
    print(f'\n== {title} ==')


# ---------------------------------------------------------------- environment

def check_python(rep: Report):
    section('Python')
    v = sys.version_info
    desc = f'Python {v.major}.{v.minor}.{v.micro} at {sys.executable}'
    if (v.major, v.minor) == (3, 12):
        rep.ok(desc)
    elif (v.major, v.minor) >= (3, 11):
        rep.warn(f'{desc} (paper results use 3.12.12)')
    else:
        rep.fail(f'{desc} is too old, use Python 3.12')


def check_packages(rep: Report):
    section('Packages (requirements.txt)')
    from importlib import metadata
    req_file = ROOT / 'requirements.txt'
    if not req_file.exists():
        rep.fail(f'{req_file} not found')
        return
    for line in req_file.read_text().splitlines():
        line = line.split('#')[0].strip()
        if not line:
            continue
        m = re.match(r'^([A-Za-z0-9_.\-]+)\s*(?:==\s*([^\s;]+))?', line)
        if not m:
            continue
        dist, pinned = m.group(1), m.group(2)
        mod = IMPORT_NAMES.get(dist.lower(), dist.replace('-', '_'))
        try:
            importlib.import_module(mod)
        except Exception as e:
            rep.fail(f'{dist}: cannot import {mod!r} ({type(e).__name__}: {e})')
            continue
        try:
            installed = metadata.version(dist)
        except metadata.PackageNotFoundError:
            installed = '?'
        if pinned and installed != pinned:
            rep.warn(f'{dist} {installed} installed, requirements.txt pins {pinned}')
        else:
            rep.ok(f'{dist} {installed}')
    import numpy
    rep.ok(f'numpy {numpy.__version__} (pulled in by the above)')

    section('Optional packages')
    for mod, why in OPTIONAL_PACKAGES.items():
        try:
            importlib.import_module(mod)
            rep.ok(f'{mod}')
        except Exception:
            rep.warn(f'{mod} missing: {why}')


def check_layout(rep: Report):
    section('Repo layout and core modules')
    for p in ['src/game_arena', 'src/experimental', 'src/game_arena/prompter_overrides.json']:
        (rep.ok if (ROOT / p).exists() else rep.fail)(p)
    if not os.access(ROOT, os.W_OK):
        rep.fail(f'{ROOT} not writable (logs/ and temp/ are written there)')
    for mod in ['game_arena.utils', 'game_arena.base', 'game_arena.run_quals', 'game_arena.run_leaderboard',
                'experimental.lm_arena.rating_systems', 'experimental.lm_arena.simple_example',
                'experimental.exp_utils', 'experimental.exp_plotting']:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                importlib.import_module(mod)
            rep.ok(f'import {mod}')
        except Exception as e:
            rep.fail(f'import {mod} ({type(e).__name__}: {e})', traceback.format_exc())
    try:
        import pyspiel
        pyspiel.load_game('tic_tac_toe').new_initial_state()
        rep.ok('pyspiel can load and create a game')
    except Exception as e:
        rep.fail(f'pyspiel smoke test ({e})', traceback.format_exc())


def get_game_list() -> list[tuple[str, str, str]]:
    """[(game, world, label)] where label is the column name used in the ELO csv."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            from experimental.exp_utils import MAIN_GAMES_WORLD_COLUMNS
        return [(g, w, label) for g, w, label, *_ in MAIN_GAMES_WORLD_COLUMNS]
    except Exception:
        return list(FALLBACK_GAMES)


def load_ratings() -> dict[str, dict[str, float]]:
    """label -> {automaton name -> ELO}. Empty if the csv is missing."""
    if not ELO_CSV.exists():
        return {}
    import pandas as pd
    df = pd.read_csv(ELO_CSV, index_col=0)
    return {col: df[col].dropna().to_dict() for col in df.columns}


# ---------------------------------------------------------------- games

def list_automata(game: str, world: str) -> dict[str, list[Path]]:
    """model -> sorted automaton dirs that contain python code."""
    from game_arena import utils
    world_dir = utils.get_examples_dir(game) / world
    out: dict[str, list[Path]] = {}
    for model_dir in sorted(world_dir.iterdir()):
        if model_dir.is_dir():
            bots = sorted(b for b in model_dir.iterdir() if (b / CODE_FILE).exists())
            if bots:
                out[model_dir.name] = bots
    return out


def compiles(bot_dir: Path) -> bool:
    from game_arena import utils
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        fn, _ = utils.get_policy_fn((bot_dir / CODE_FILE).read_text(), bot_dir / CODE_FILE, bot_dir.name)
    return fn is not None


def pick_bots(bots: list[Path], k: int, rng: random.Random) -> list[Path]:
    bots = list(bots)
    rng.shuffle(bots)
    return [b for b in bots if compiles(b)][:k]


def engine_smoke_test(game: str, world: str) -> int:
    """Play one random game in-process directly on the engine. Returns number of plies."""
    from game_arena import utils
    game_cls = utils.get_game(game)
    g = game_cls(utils.get_config_file(game, world))
    random_policy = utils.get_the_random_policy()
    for ply in range(100_000):
        if g.is_done():
            g.get_final_stats()
            return ply
        g.get_observation()
        assert g.current_player() in (0, 1), f'bad current player {g.current_player()}'
        legal = g.get_legal_moves()
        assert len(legal) > 0, 'no legal moves in a non-terminal state'
        move_str = random_policy(_debug_legal_moves=legal)
        g.game_step(g.get_move(move_str))
    raise AssertionError('random game did not terminate after 100000 plies')


def build_matchups(game: str, world: str, n_pairs: int, rng: random.Random, ratings: dict[str, float]):
    """Returns [(kind, botpath0, botpath1), ...] with each pairing played from both sides.

    Automata are drawn from the top half of the tournament ratings when available, since a large
    share of automata from weak models make illegal moves or time out, which says nothing about
    the installation.
    """
    all_by_model = list_automata(game, world)
    ex = (SRC / 'game_arena' / game / 'examples' / world)
    by_model = all_by_model
    if ratings:
        cutoff = sorted(ratings.values())[len(ratings) // 2]
        strong = {n for n, r in ratings.items() if r >= cutoff}
        filtered = {m: [b for b in bots if f'{m}/{b.name}' in strong] for m, bots in all_by_model.items()}
        filtered = {m: bots for m, bots in filtered.items() if bots}
        if len(filtered) >= 2:
            by_model = filtered
    rand = ('random', None)

    def bp(path: Path):
        return (path.relative_to(ex).as_posix(), path)

    pairs = [('random_vs_random', rand, rand)]
    models = list(by_model)
    rng.shuffle(models)
    singles = []
    for m in models:
        singles += pick_bots(by_model[m], 1, rng)
        if len(singles) >= max(2, n_pairs + 1):
            break
    for b in singles[:n_pairs]:
        pairs.append(('automaton_vs_random', bp(b), rand))
    multi = [m for m in models if len(by_model[m]) >= 2]
    for m in multi:
        two = pick_bots(by_model[m], 2, rng)
        if len(two) == 2:
            pairs.append(('quals_pair', bp(two[0]), bp(two[1])))
            break
    for i in range(min(n_pairs, len(singles) - 1)):
        pairs.append(('tourney_pair', bp(singles[i]), bp(singles[i + 1])))
    matchups = []
    for kind, a, b in pairs:
        matchups += [(kind, a, b), (kind, b, a)]
    return matchups, sum(len(v) for v in all_by_model.values()), len(all_by_model)


def run_matches(rep: Report, games: list[tuple[str, str]], n_pairs: int, timeout: int, workers: int, seed: int):
    from game_arena import base, utils
    section('Game engines')
    jobs = []
    try:
        ratings = load_ratings()
    except Exception as e:
        rep.warn(f'could not read {ELO_CSV.name} ({e}), sampling automata uniformly')
        ratings = {}
    for game, world, label in games:
        name = f'{game}/{world}'
        try:
            plies = engine_smoke_test(game, world)
        except Exception as e:
            rep.fail(f'{name}: engine smoke test ({type(e).__name__}: {e})', traceback.format_exc())
            continue
        try:
            matchups, n_bots, n_models = build_matchups(game, world, n_pairs, random.Random(f'{seed}{name}'), ratings.get(label, {}))
        except Exception as e:
            rep.fail(f'{name}: could not list automata ({e})', traceback.format_exc())
            continue
        if n_bots == 0:
            rep.fail(f'{name}: no automata found')
        rep.ok(f'{name}: random game in {plies} plies, {n_bots} automata from {n_models} models')
        game_cls = utils.get_game(game)
        config = utils.get_config_file(game, world)
        for i, (kind, a, b) in enumerate(matchups):
            jobs.append((name, kind, game_cls, config, [a, b], seed + i))

    section(f'Matches ({len(jobs)} games, timeout {timeout}s per move, {workers} workers)')
    results: dict[str, list] = {}
    fatal: dict[str, list[str]] = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(base.play_game_with_timeout, gc, cfg, bots, s, timeout): (name, kind)
                for name, kind, gc, cfg, bots, s in jobs}
        for done, fut in enumerate(as_completed(futs), 1):
            name, kind = futs[fut]
            try:
                results.setdefault(name, []).append((kind, fut.result()))
            except Exception:
                fatal.setdefault(name, []).append(traceback.format_exc())
            if sys.stdout.isatty():
                print(f'\r  {DIM}{done}/{len(jobs)} games finished, {time.time() - t0:.0f}s{RESET}', end='', flush=True)
    print(f'\r  {len(jobs)} games played in {time.time() - t0:.0f}s')

    all_matches = []
    for game, world, _ in games:
        name = f'{game}/{world}'
        if name not in results and name not in fatal:
            continue
        if name in fatal:
            rep.fail(f'{name}: {len(fatal[name])} match(es) crashed the runner', fatal[name][0])
        played = results.get(name, [])
        counts = {'done': 0, 'error': 0, 'timeout': 0}
        problems = []
        for kind, m in played:
            outcome = 'done' if m['done'] else m['winner']
            counts[outcome] = counts.get(outcome, 0) + 1
            try:
                utils.get_player_result(m, 0, verbose=False)
            except Exception as e:
                problems.append(f'unparseable result ({e})')
            if kind == 'random_vs_random' and not m['done']:
                problems.append(f'random vs random did not finish: {m["winner"]} {m.get("exception", "")}'.strip())
        auto = [m for kind, m in played if kind != 'random_vs_random']
        if auto and not any(m['done'] for m in auto):
            problems.append('no match involving an automaton finished normally')
        summary = f'{len(played)} games: {counts["done"]} finished, {counts["error"]} automaton errors, {counts["timeout"]} timeouts'
        if problems:
            rep.fail(f'{name}: {summary}', '\n'.join(sorted(set(problems))))
        else:
            rep.ok(f'{name}: {summary}')
        all_matches += [m for _, m in played]
    return all_matches


def check_ratings(rep: Report, matches: list):
    section('Rating code')
    if not matches:
        rep.warn('no matches to rate')
        return
    from game_arena import base, run_quals
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            elo = base.get_bt_elo_ratings(matches)
        assert len(elo) > 0
        rep.ok(f'BT ELO computed for {len(elo)} players')
    except Exception as e:
        rep.fail(f'BT ELO ({type(e).__name__}: {e})', traceback.format_exc())
    quals = [m for m in matches if m['name0'] != 'random' and m['name1'] != 'random'
             and m['name0'].split('/')[0] == m['name1'].split('/')[0]]
    if not quals:
        rep.warn('no quals style matches to compute CI rankings on')
        return
    try:
        parents = sorted({m['name0'].split('/')[0] for m in quals})
        with contextlib.redirect_stdout(io.StringIO()):
            ci = run_quals.get_ci_rankings(quals, parent=parents)
        assert set(ci) == set(parents), f'{set(ci)} != {set(parents)}'
        rep.ok(f'quals CI rankings computed for {len(ci)} models')
    except Exception as e:
        rep.fail(f'quals CI rankings ({type(e).__name__}: {e})', traceback.format_exc())


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--games', default=None, help='comma separated game or game/world names (default: all main games)')
    parser.add_argument('--n-pairs', type=int, default=2, help='automaton vs random and cross model pairs per game (each played from both sides)')
    parser.add_argument('--timeout', type=int, default=1, help='per move timeout in seconds, same meaning as in quals/tourney')
    parser.add_argument('--workers', type=int, default=min(32, os.cpu_count() or 4))
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--skip-matches', action='store_true', help='only check the environment and imports')
    args = parser.parse_args()

    sys.path.insert(0, str(SRC))
    os.chdir(SRC)  # README runs everything from src/
    os.environ.setdefault('PYTHONHASHSEED', '0')

    rep = Report()
    t0 = time.time()
    check_python(rep)
    check_packages(rep)
    check_layout(rep)

    if not args.skip_matches:
        games = get_game_list()
        if args.games:
            wanted = [s.strip() for s in args.games.split(',') if s.strip()]
            games = [(g, w, label) for g, w, label in games if g in wanted or f'{g}/{w}' in wanted]
            if not games:
                rep.fail(f'--games {args.games} matched none of the main games')
        if games:
            try:
                matches = run_matches(rep, games, args.n_pairs, args.timeout, args.workers, args.seed)
                check_ratings(rep, matches)
            except Exception as e:
                rep.fail(f'match runner ({type(e).__name__}: {e})', traceback.format_exc())

    section('Summary')
    print(f'  {len(rep.failures)} failures, {len(rep.warnings)} warnings, {time.time() - t0:.0f}s')
    for f in rep.failures:
        print(f'  {RED}FAIL{RESET}  {f}')
    if rep.failures:
        print(f'\n{RED}Installation is NOT working.{RESET}')
        sys.exit(1)
    print(f'\n{GREEN}Installation verified.{RESET}')


if __name__ == '__main__':
    main()

"""Runs public/arena.runner.py (the Python the browser executes in Pyodide) under CPython against
src/game_arena, the same engines the browser loads. Covers audit issues 1 and 2.

    cd src && ../env3.12/bin/python -m pytest frontend/arena_fe/test/python -q
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[4]
RUNNER = SRC / "frontend" / "arena_fe" / "public" / "arena.runner.py"
sys.path.insert(0, str(SRC))

from game_arena import utils  # noqa: E402

GAME_WORLDS = [
    "tic_tac_toe/world1", "tic_tac_toe/world2", "tic_tac_toe_3d/world1", "battleships/world1",
    "connect4/world1", "mancala/world1", "othello/world1", "lines_of_action/world1", "pentago/world1",
    "clobber/world1", "amazons/world1", "backgammon/world1", "nim/world1", "dots_and_boxes/world1",
    "chess/worlduci1", "go/world1", "checkers/world1", "havannah/world1", "hex/world1", "breakthrough/world1",
]
QUAL_SEEDS = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]  # entrypoints-create.component.ts

FIRST_LEGAL_STR = """
def policy(_debug_legal_moves, **kw):
    m = _debug_legal_moves[0]
    return m.get_unparsed_str() if hasattr(m, "get_unparsed_str") else m
"""
FIRST_LEGAL_RAW = """
def policy(_debug_legal_moves, **kw):
    return _debug_legal_moves[0]
"""
TTT_FIRST_EMPTY = """
def policy(board):
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == 0:
                return (r, c)
"""
TTT_FIRST_EMPTY_STR = """
def policy(board):
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == 0:
                return f"{r},{c}"
"""
TTT_CONSTANT = "def policy(board): return (0, 0)\n"
NIM_AUDIT = "def policy(piles):\n    return next(f'{i},1' for i, n in enumerate(piles) if n)\n"
CONNECT4_FIRST_INT = "def policy(_debug_legal_moves, **kw):\n    return int(_debug_legal_moves[0])\n"


@pytest.fixture()
def runner():
    """A fresh runner namespace per test, like a fresh Pyodide runtime."""
    ns = {"__name__": "arena_runner"}
    exec(compile(RUNNER.read_text(), str(RUNNER), "exec"), ns)
    return ns


def _split(gw):
    game, world = gw.split("/")
    return game, world, utils.get_config_file(game, world)


def _compile(runner, game, world, cfg, code):
    res = runner["set_user_policy"](game, world, code, cfg, True)
    assert res["ok"], f"{game}/{world}: valid policy failed to compile: {res.get('error')}"


def _qualify(runner, game, world, cfg, seeds=QUAL_SEEDS):
    """Same seat/seed schedule as the Create page's qualification against random."""
    out = []
    for i, seed in enumerate(seeds):
        side = i % 2
        a, b = ("user", "random") if side == 0 else ("random", "user")
        out.append((side, runner["play_full_match"](game, world, cfg, a, b, seed, None)))
    return out


def _assert_no_faults(gw, results):
    for side, r in results:
        assert r.get("culprit") is None, (
            f"{gw}: {r.get('culprit_name')} faulted after {r.get('moves')} moves: {r.get('error')}"
        )
        assert r.get("reason") in ("win", "draw"), f"{gw}: unexpected reason {r.get('reason')}: {r.get('error')}"


# ---- issue 1: move conversion -------------------------------------------------------------

@pytest.mark.parametrize("gw", GAME_WORLDS)
def test_random_baseline_plays_legal_games(runner, gw):
    game, world, cfg = _split(gw)
    for seed in (42, 43):
        r = runner["play_full_match"](game, world, cfg, "random", "random", seed, None)
        _assert_no_faults(gw, [(0, r)])


@pytest.mark.parametrize("gw", GAME_WORLDS)
@pytest.mark.parametrize("code", [FIRST_LEGAL_STR, FIRST_LEGAL_RAW], ids=["serialized", "already-parsed"])
def test_first_legal_policy_compiles_and_qualifies(runner, gw, code):
    game, world, cfg = _split(gw)
    _compile(runner, game, world, cfg, code)
    _assert_no_faults(gw, _qualify(runner, game, world, cfg, QUAL_SEEDS[:4]))


@pytest.mark.parametrize("gw,code", [
    ("tic_tac_toe/world1", TTT_FIRST_EMPTY),
    ("tic_tac_toe/world1", TTT_FIRST_EMPTY_STR),
    ("tic_tac_toe/world2", TTT_FIRST_EMPTY),
    ("nim/world1", NIM_AUDIT),
    ("connect4/world1", CONNECT4_FIRST_INT),
], ids=["ttt-tuple", "ttt-string", "ttt4-tuple", "nim-string", "connect4-int"])
def test_audit_policies_qualify_without_faults(runner, gw, code):
    game, world, cfg = _split(gw)
    _compile(runner, game, world, cfg, code)
    _assert_no_faults(gw, _qualify(runner, game, world, cfg))


def test_constant_policy_faults_on_occupied_cell(runner):
    """A real user fault must stay a user fault: (0, 0) is illegal once the cell is taken."""
    game, world, cfg = _split("tic_tac_toe/world1")
    _compile(runner, game, world, cfg, TTT_CONSTANT)
    for side, r in _qualify(runner, game, world, cfg):
        assert r.get("culprit_name") == "user", f"seat {side}: expected a user fault, got {r}"
        assert r.get("reason") == "illegal"
        assert r["moves"] >= 1, "the fault can only come once (0, 0) is occupied"


@pytest.mark.parametrize("gw", ["tic_tac_toe/world1", "nim/world1", "connect4/world1"])
def test_broken_baseline_is_not_reported_as_opponent_fault(runner, gw, monkeypatch):
    """If the random baseline itself cannot play, that is an infrastructure error, not a win."""
    game, world, cfg = _split(gw)
    _compile(runner, game, world, cfg, FIRST_LEGAL_STR)
    real_get_game = utils.get_game

    def broken_get_game(name):
        cls = real_get_game(name)

        class Broken(cls):  # type: ignore[misc, valid-type]
            def get_move(self, move_str):
                if self.current_player() == 1:
                    raise RuntimeError("simulated baseline breakage")
                return super().get_move(move_str)

        return Broken

    monkeypatch.setattr(utils, "get_game", broken_get_game)
    r = runner["play_full_match"](game, world, cfg, "user", "random", 42, None)
    assert not (r.get("culprit_name") == "random" and r.get("winner") == 0), (
        f"broken baseline was scored as a user win: {r}"
    )


# ---- issue 2: NumPy moves, record -> serialize -> replay ------------------------------------

NP_TTT = "def policy(board):\n    return tuple(np.argwhere(np.array(board) == 0)[0])\n"
NP_TTT3D = """
def policy(_debug_legal_moves, **kw):
    m = _debug_legal_moves[0]
    return tuple(np.int64(int(x)) for x in m.get_unparsed_str().strip("()").split(","))
"""
NP_CONNECT4 = "def policy(_debug_legal_moves, **kw):\n    return np.int64(int(_debug_legal_moves[0]))\n"
NP_NIM = "def policy(piles):\n    i = int(np.flatnonzero(np.array(piles))[0])\n    return np.str_(f'{i},1')\n"


def test_move_to_json_normalizes_numpy(runner):
    to_json = runner["_move_to_json"]
    assert to_json((np.int64(0), np.int32(2))) == [0, 2]
    assert to_json([np.int64(1), (np.int64(2), np.int8(3))]) == [1, [2, 3]]
    assert to_json(np.int64(4)) == 4 and type(to_json(np.int64(4))) is int
    assert to_json(np.bool_(True)) is True
    assert to_json("3,4") == "3,4", "legitimate string moves must stay strings"
    assert to_json(np.str_("0,1")) == "0,1"


BACKGAMMON_HL = r"""
def policy(state, _debug_legal_moves, **kw):
    d = state["dice"]
    def enc(f):
        return "B" if f == "BAR" else f"A{f-1}"
    import re
    for m in _debug_legal_moves:
        toks = str(m).split(" - ")[-1].split()
        if len(toks) != 2 or not all(re.fullmatch(r"\d+/\d+", t) for t in toks):
            continue
        (f1, t1), (f2, t2) = [tuple(int(x) for x in t.split("/")) for t in toks]
        j1 = f1 - t1
        if j1 == d[1]:
            return f"H:{enc(f1)},{enc(f2)}"
        if j1 == d[0]:
            return f"L:{enc(f1)},{enc(f2)}"
    m = _debug_legal_moves[0]
    return m.get_unparsed_str() if hasattr(m, "get_unparsed_str") else m
"""


@pytest.mark.parametrize("gw,code", [
    ("tic_tac_toe/world1", TTT_FIRST_EMPTY),
    ("tic_tac_toe/world1", NP_TTT),
    ("tic_tac_toe_3d/world1", NP_TTT3D),
    ("connect4/world1", NP_CONNECT4),
    ("nim/world1", NP_NIM),
    ("hex/world1", FIRST_LEGAL_STR),
    ("backgammon/world1", BACKGAMMON_HL),
], ids=["ttt-native", "ttt-numpy", "ttt3d-numpy", "connect4-numpy", "nim-numpy-str", "hex-string", "backgammon-hl"])
def test_recorded_match_replays_to_same_outcome(runner, gw, code):
    game, world, cfg = _split(gw)
    _compile(runner, game, world, cfg, code)
    live = runner["play_full_match"](game, world, cfg, "user", "user", 42, None)
    assert live.get("culprit") is None, live
    history = json.loads(json.dumps(live["history"]))
    replay = runner["replay_moves"](game, world, cfg, 42, history)
    assert replay["failed_move"] is None, f"replay rejected a recorded move: {replay['failed_move']}"
    assert replay["applied"] == replay["total"] == live["moves"]
    assert replay["done"]
    assert replay["final"].get("winner") == live["final"].get("winner")

import sys
import json
import math
import random
import inspect
import logging
import traceback
import warnings
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Union, Callable, Optional, Any

import numpy as np

from game_arena.typing import Player, PolicyFn


_GLOBAL_CACHE = {}


def get_root_path():
    result = Path(__file__).parent.parent.parent
    assert (result / 'src').exists(), f"Root path not found {result}"
    return result


def get_game_arena_dir():
    return get_root_path() / 'src' / 'game_arena'


def get_game_dir(game_str: str):
    return get_game_arena_dir() / game_str


def get_examples_dir(game_str: str):
    return get_game_arena_dir() / game_str / 'examples'


def get_config_file(game_str: str, world: str):
    world_dir = get_examples_dir(game_str) / world
    config_path = world_dir / 'config.json'
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}
    return config


def get_temp_path(unique_id: str):
    result = get_root_path() / 'temp' / unique_id
    result.mkdir(parents=True, exist_ok=True)
    return result


def get_logs_dir():
    return get_root_path() / 'logs'


def set_seed(seed: Optional[int] = None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)


def setup_logging(filename: Union[str, Path], logger_name: str, to_stdout: bool = False, stdout_level: int = logging.INFO, rotate: bool = False) -> logging.Logger:
    if isinstance(filename, str):
        p = get_logs_dir() / filename
    else:
        p = filename
    p.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")
    if not any(getattr(h, "baseFilename", None) == str(p) for h in logger.handlers):
        if rotate:
            print('CREATING ROTATING HANDLER', str(p))
            p_pre, p_post = str(p).rsplit('.', 1)
            p = p_pre + '_' + datetime.now().strftime('%Y_%m_%d') + '.' + p_post
        fh = logging.FileHandler(str(p))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    if to_stdout and not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
                             for h in logger.handlers):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(stdout_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def get_game(game_name: str):
    if game_name == 'tic_tac_toe_3d':
        from game_arena.tic_tac_toe_3d import game
        return game.TicTacToe3D
    if game_name == 'tic_tac_toe':
        from game_arena.tic_tac_toe import game
        return game.TicTacToeGame
    if game_name == 'blackjack':
        from game_arena.blackjack import game
        return game.BlackjackGame
    if game_name == 'battleships':
        from game_arena.battleships import game
        return game.BattleshipGame
    if game_name == 'connect4':
        from game_arena.connect4 import game
        return game.Connect4Game
    if game_name == 'lines_of_action':
        from game_arena.lines_of_action import game
        return game.LinesOfActionGame
    if game_name == 'mancala':
        from game_arena.mancala import game
        return game.MancalaGame
    if game_name == 'pentago':
        from game_arena.pentago import game
        return game.PentagoGame
    if game_name == 'clobber':
        from game_arena.clobber import game
        return game.ClobberGame
    if game_name == 'amazons':
        from game_arena.amazons import game
        return game.AmazonsGame
    if game_name == 'dots_and_boxes':
        from game_arena.dots_and_boxes import game
        return game.DotsAndBoxesGame
    if game_name == 'backgammon':
        from game_arena.backgammon import game
        return game.BackgammonGame
    if game_name == 'nim':
        from game_arena.nim import game
        return game.NimGame
    if game_name == 'poker':
        from game_arena.poker import game
        return game.PokerGame
    if game_name == 'phantom_ttt':
        from game_arena.phantom_ttt import game
        return game.PhantomTTTGame
    if game_name == 'chess':
        from game_arena.chess import game
        return game.ChessGame
    if game_name == 'go':
        from game_arena.go import game
        return game.GoGame
    if game_name == 'checkers':
        from game_arena.checkers import game
        return game.CheckersGame
    if game_name == 'havannah':
        from game_arena.havannah import game
        return game.HavannahGame
    if game_name == 'hex':
        from game_arena.hex import game
        return game.HexGame
    if game_name == 'breakthrough':
        from game_arena.breakthrough import game
        return game.BreakthroughGame
    if game_name == 'othello':
        from game_arena.othello import game
        return game.OthelloGame
    if game_name == 'stanford_gamemaster':
        from game_arena.stanford_gamemaster import game
        return game.StanfordGameMasterGame
    raise ValueError(f'Unknown game {game_name}')

def callable_name(obj: Any) -> str:
    name = getattr(obj, "__name__", None)
    if isinstance(name, str) and name:
        return name
    func = getattr(obj, "func", None)
    func_name = getattr(func, "__name__", None)
    if isinstance(func_name, str) and func_name:
        return f"partial({func_name})"
    return type(obj).__name__


def get_policy_fn(code: str, py_code: Union[Path, str], print_path: str):
    ns = {"np": np, "random": random, '__file__': str(py_code)}
    msg = None
    # compile just to give it a filename in tracebacks
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            exec(compile(code, str(py_code), 'exec'), ns)
    except Exception as e:
        msg = f"    Error compiling policy {print_path}: {e}"
        traceback.print_exc()
        return None, msg
    policy_fn = ns.get('policy')
    if policy_fn is None or not callable(policy_fn):
        msg = f"    Error finding policy {print_path}: {policy_fn} is not a callable"    
        return None, msg
    return policy_fn, msg


def wrap_policy_fn_with_memory(policy_fn: Callable) -> Callable:
    """Ugly hack to inject memory into the policy functions that accept it as an argument.
    This is used to allow the policy functions to use memory to store information between calls.
    Policies that accept memory as an argument MUST return two outputs: an action and a new memory state.
    """
    memory = {}
    assert callable(policy_fn), 'policy_fn must be a callable'
    param_names = [param.name for param in inspect.signature(policy_fn).parameters.values()]
    if 'memory' not in param_names:
        return policy_fn
    else:
        def wrapped_policy_fn(**kwargs):
            nonlocal memory
            assert 'memory' not in kwargs, 'memory already in kwargs???'
            kwargs['memory'] = memory
            action, new_memory = policy_fn(**kwargs)
            memory = new_memory
            return action
        return wrapped_policy_fn



def get_bot_jsons(ex: Path):
    assert ex.exists()
    results: dict[str, PolicyFn] = {}
    for model_dir in ex.iterdir():
        if not model_dir.is_dir():
            continue
        bot_count = 0
        for b in sorted(model_dir.iterdir()):
            if not b.is_dir():
                continue
            py_code = (b / '2.python_code.py')
            if not py_code.exists():
                continue
            with open(py_code, 'r') as f:
                code = f.read()
            relative_path = b.relative_to(ex).as_posix()
            if code in _GLOBAL_CACHE:
                results[relative_path] = _GLOBAL_CACHE[code]
                bot_count += 1
                continue
            policy_fn, msg = get_policy_fn(code, py_code, relative_path)
            if policy_fn is None:
                if msg is not None:
                    print(msg)
                continue
            policy_fn = wrap_policy_fn_with_memory(policy_fn)  # type: ignore
            results[relative_path] = policy_fn
            bot_count += 1
            _GLOBAL_CACHE[code] = policy_fn
    return results


def get_bot_paths(ex: Path, allowed_bot_nums: Optional[list[int]] = None):
    assert ex.exists()
    results: dict[str, Path] = {}
    for model_dir in ex.iterdir():
        if not model_dir.is_dir():
            continue
        bot_count = 0
        for b in sorted(model_dir.iterdir()):
            if not b.is_dir():
                continue
            py_code = (b / '2.python_code.py')
            if not py_code.exists():
                continue
            with open(py_code, 'r') as f:
                code = f.read()
            relative_path = b.relative_to(ex).as_posix()
            policy_fn, msg = get_policy_fn(code, py_code, relative_path)
            if policy_fn is None:
                if msg is not None:
                    print(msg)
                continue
            bot_count += 1  # bot successfully loaded!
            # only add it if its allowed, otherwise skip
            if allowed_bot_nums is not None and bot_count not in allowed_bot_nums:
                continue
            results[relative_path] = b
    return results


def get_the_random_policy() -> PolicyFn:
    def random_policy(_debug_legal_moves, **kwargs):
        r = random.choice(_debug_legal_moves)
        if hasattr(r, 'get_unparsed_str'):
            return r.get_unparsed_str()
        else:
            return r
    return random_policy


def _allowed_list_from_str(s: Optional[str]) -> Optional[list[int]]:
    if s is None or s == '':
        return None
    return [int(i) for i in s.split(',')]


def get_bot_jsons_from_world(game: str, world: str, add_random: bool = False) -> dict[str, PolicyFn]:
    ex = get_examples_dir(game) / world
    if not ex.exists():
        print(f"No world directory found for {game} {world}")
        return {}
    result = get_bot_jsons(ex)
    if add_random:
        result['random'] = get_the_random_policy()
    return result


def get_bot_paths_from_world(game: str, world: str, add_random: bool = False, allowed_bot_nums: Optional[str] = None) -> dict[str, Path]:
    ex = get_examples_dir(game) / world
    if not ex.exists():
        print(f"No world directory found for {game} {world}")
        return {}
    result = get_bot_paths(ex, allowed_bot_nums=_allowed_list_from_str(allowed_bot_nums))
    if add_random:
        result['random'] = None  # type: ignore
    return result

def get_policy_fn_with_memory(name: str, path: Union[Path, Callable]) -> Player:
    if callable(path):
        return name, path
    if name == 'random':
        return name, get_the_random_policy()
    assert isinstance(path, Path), f"Path must be a Path object or a callable. Got {type(path)}"
    py_code = path if path.is_file() else (path / "2.python_code.py")
    assert py_code.exists(), f"Python code not found for {name} at {path}"
    with open(py_code, 'r') as f:
        code = f.read()
    policy_fn, msg = get_policy_fn(code, py_code, path.as_posix())
    assert policy_fn is not None, f"Failed to get policy function for {name} at {path}: {msg}"
    policy_fn = wrap_policy_fn_with_memory(policy_fn)  # type: ignore
    return name, policy_fn


def _get_timeout_winner(time_analysis: dict[str, float], verbose: bool = False) -> tuple[str, float]:
    # sum the last as additional time
    time_p0 = time_analysis.get('0', 0)
    time_p1 = time_analysis.get('1', 0)
    last_player, last_time = time_analysis['last']  # type: ignore
    if last_player == '0':
        time_p0 += last_time
    elif last_player == '1':
        time_p1 += last_time
    else:
        assert False, f"Unknown last player: {last_player}"
    # not_last_players = '1' if last_player == '0' else '0'
    # if verbose and time_analysis.get(not_last_players, 0) > time_analysis.get(last_player, 0):
    #     print('WARNING: edge case where the last player in a timeout was not the cause of the timeout', match)
    if verbose and time_p0 + time_p1 < 3:
        print(f'WARNING: total time < 3 seconds. Total time: {time_p0 + time_p1:.1f} seconds. time_analysis: {time_analysis}')
    # else:
    #     print(f'Good. Total time: {time_p0 + time_p1:.1f} seconds. Match:', match)
    assert time_p0 != time_p1, "Time is the same for both players"
    winner = 1 if time_p1 < time_p0 else 0
    return ('timeout', winner)

_DEBUG_PRINT_LIMIT = 6
def get_match_result(match: dict[str, Any], verbose: bool) -> tuple[str, float]:
    # returns who won and due to what reason, a draw is ('draw', None). The input "match" is the dict which is 1 element of all_data.
    if match['done'] and match['winner'] is not None:
        return ('win', match['winner'])
    elif match['done'] and match['winner'] is None:
        return ('draw', 0.5)
    elif match['winner'] == 'error' and match['r'] and 'player_err_counts' in match['r'] and set(match['r']['player_err_counts']) == {0, 1}:
        return ('error', match['r']['player_err_counts'].index(0))
    elif match['winner'] == 'timeout' and 'timeout_hit' in match:
        loser = int(match['timeout_hit'][0])
        assert loser in (0, 1), f"Invalid timeout_player: {match}"
        return ('timeout', 1 - loser)
    elif match['winner'] == 'timeout' and 'time_analysis' in match:  # LEGACY
        global _DEBUG_PRINT_LIMIT
        _DEBUG_PRINT_LIMIT -= 1
        if _DEBUG_PRINT_LIMIT > 0:
            print('LEGACY', match)
        elif _DEBUG_PRINT_LIMIT == 0:
            print('LEGACY no longer printing')
        time_analysis = match['time_analysis']
        return _get_timeout_winner(time_analysis, verbose)
    else:
        assert False, f"Unknown match result: {match}"

def get_player_result(match: dict[str, Any], player_idx: int, verbose: bool) -> str:
    # returns the result of the player with index player_idx; either 'win', 'loss', 'draw', 'error', 'timeout', 'enemy_error', 'enemy_timeout'
    reason, winner = get_match_result(match, verbose)
    # print(winner, player_idx)
    if reason == 'win':
        return 'win' if winner == player_idx else 'loss'
    elif reason == 'draw':
        return 'draw'
    elif reason == 'error' and winner != player_idx:
        return 'error'
    elif reason == 'error' and winner == player_idx:
        return 'enemy_error'
    elif reason == 'timeout' and winner != player_idx:
        return 'timeout'
    elif reason == 'timeout' and winner == player_idx:
        return 'enemy_timeout'
    else:
        assert False, f"Unknown match result: {match}"


def infer_elo(games: list[tuple[str, str, float]], K=32.0, s=400, kappa=2.0, base_rating=1500, iters=20):
    players = set()
    games_list = list(games)
    for a, b, _ in games_list:
        assert isinstance(a, str) and isinstance(b, str), "Players must be strings"
        players.add(a)
        players.add(b)
    ratings = {p: 0.0 for p in players}
    def g(r):
        pow_r_s = 10.0 ** (r / s)
        return (pow_r_s + kappa/2.0) / (10.0 ** (-r / s) + kappa + pow_r_s)
    for _ in range(iters):
        old_ratings = ratings.copy()
        for a, b, result_A in games_list:
            assert result_A in {1, 0.5, 0}, "Result must be 1, 0.5, or 0"
            if a == b:
                continue
            Ra = ratings[a]
            Rb = ratings[b]
            diff = Ra - Rb

            expected_A = g(diff)
            change = K * (result_A - expected_A)
            ratings[a] += change
            ratings[b] -= change
    allowed_percent_change_l1 = 1e-4
    l1_change = sum(abs(ratings[p] - old_ratings[p]) for p in ratings)
    l1_base   = max(1e-9, sum(abs(old_ratings[p]) for p in ratings))  # avoid div by 0
    if l1_change / l1_base > allowed_percent_change_l1:
        print(f'Warning: last iteration changed more than allowed_percent_change_l1: {l1_change / l1_base:.5f}')
    mean_rating = sum(ratings.values()) / len(ratings)
    shift = base_rating - mean_rating
    for p in ratings:
        ratings[p] += shift
    return ratings


def infer_glicko1(
        games: list[tuple[str, str, float]],  # (player_A, player_B, result_for_A) where result ∈ {1, 0.5, 0}
        *,
        base_rating: float = 1500.0,
        base_rd: float = 350.0,
        c: float = 0.0,
        rd_max: float = 350.0,
        return_rd: bool = False,
    ) -> Union[dict[str, float], tuple[dict[str, float], dict[str, float]]]:
    """
    Glicko-1 inference treating ALL provided games as ONE rating period.

    Inputs:
      games: list of (A, B, result_for_A) where result_for_A ∈ {1, 0.5, 0}.
      base_rating: after computing relative ratings, shift so mean == base_rating.
      base_rd: initial rating deviation for all players.
      c: RD "aging" per rating period (0 disables aging). Typical values depend on your period length.
      rd_max: maximum RD (standard is 350).
      return_rd: if True, return (ratings, rds); else return ratings only.

    Notes:
      - Glicko-1 normally returns both rating and RD; RD is the uncertainty.
      - Shifting the mean rating does not affect expected outcomes; it’s just anchoring.
    """
    # Collect players
    players = set()
    for a, b, _ in games:
        if not isinstance(a, str) or not isinstance(b, str):
            raise TypeError("Players must be strings")
        players.add(a)
        players.add(b)

    # Build per-player match lists
    matches = defaultdict(list)  # p -> list[(opp, score_for_p)]
    for a, b, result_a in games:
        if result_a not in (0.0, 0.5, 1.0):
            raise ValueError("Result must be 1, 0.5, or 0")
        if a == b:
            continue
        matches[a].append((b, float(result_a)))
        matches[b].append((a, float(1.0 - result_a)))

    # Initialize relative ratings at 0; we'll shift to base_rating at the end.
    r = {p: 0.0 for p in players}
    rd = {p: float(base_rd) for p in players}

    # Constants
    q = math.log(10.0) / 400.0
    pi2 = math.pi ** 2

    def g(rd_opp: float) -> float:
        # g(RD) in Glicko-1
        return 1.0 / math.sqrt(1.0 + (3.0 * q * q * rd_opp * rd_opp) / pi2)

    def E(r_i: float, r_j: float, rd_j: float) -> float:
        # Expected score for i vs j
        gj = g(rd_j)
        return 1.0 / (1.0 + 10.0 ** (-(gj * (r_i - r_j) / 400.0)))

    # Pre-rating-period RD (aging / time passing)
    pre_rd = {}
    for p in players:
        aged = math.sqrt(rd[p] * rd[p] + c * c)
        pre_rd[p] = min(float(rd_max), aged)

    # One rating-period update (simultaneous, based on pre-period r and pre_rd)
    new_r = dict(r)
    new_rd = dict(pre_rd)

    for p in players:
        if not matches[p]:
            # No games: rating unchanged, RD just ages (already in pre_rd)
            continue

        r_p = r[p]
        rd_p = pre_rd[p]

        # Compute d^2 (a.k.a. v) and the rating update numerator
        sum_g2_E_1mE = 0.0
        sum_g_s_minus_E = 0.0

        for opp, score in matches[p]:
            r_o = r[opp]
            rd_o = pre_rd[opp]
            gj = g(rd_o)
            Ej = 1.0 / (1.0 + 10.0 ** (-(gj * (r_p - r_o) / 400.0)))
            sum_g2_E_1mE += (gj * gj) * Ej * (1.0 - Ej)
            sum_g_s_minus_E += gj * (score - Ej)

        # If numerical issues arise (e.g., all Ej are 0/1), skip update safely
        if sum_g2_E_1mE <= 0.0:
            continue

        d2 = 1.0 / (q * q * sum_g2_E_1mE)

        denom = (1.0 / (rd_p * rd_p)) + (1.0 / d2)
        # New RD
        rd_new = math.sqrt(1.0 / denom)
        # New rating
        r_new = r_p + (q / denom) * sum_g_s_minus_E

        new_r[p] = r_new
        new_rd[p] = min(float(rd_max), rd_new)

    # Shift ratings so mean == base_rating (pure anchoring)
    mean_rating = sum(new_r.values()) / max(1, len(new_r))
    shift = base_rating - mean_rating
    for p in new_r:
        new_r[p] += shift

    if return_rd:
        return new_r, new_rd
    return new_r


def infer_elo2(
    games: list[tuple[str, str, float]],
    K: float = 32,
    s: float = 4000,
    kappa: float = 2.0,
    base_rating: float = 1500,
    iters: int = 20,
) -> dict[str, float]:
    """
    THIS FUNCTION WAS GENERATED BY GPT AND IT ONLY TO CONFIRM THAT THE ABOVE CALCULATION IS CORRECT.
    Infer Elo-style ratings for win/draw/loss games using the Elo-Davidson update
    described in Wikipedia's "Formal derivation for win/draw/loss games".

    Parameters
    ----------
    games:
        List of (player_a, player_b, score_a) where score_a is from A's perspective:
        1.0 = A wins, 0.5 = draw, 0.0 = A loses.
    K:
        Step size (the Elo K-factor) for each game update.
    s:
        Elo scaling parameter (commonly 400). Appears in 10^(r/s).
    kappa:
        Draw propensity parameter (>= 0). Higher => more draws in the model.
    base_rating:
        Initial rating for any unseen player.
    iters:
        Number of passes over the full games list.

    Returns
    -------
    Dict[str, float]:
        Ratings by player name.
    """
    if iters < 1:
        raise ValueError("iters must be >= 1")
    if s <= 0:
        raise ValueError("s must be > 0")
    if kappa < 0:
        raise ValueError("kappa must be >= 0")

    def g(r: float) -> float:
        """
        Expected fractional score for player A under the Elo-Davidson adjacent-categories model:
            g(r; kappa) = (10^(r/s) + kappa/2) / (10^(-r/s) + kappa + 10^(r/s))
        where r = R_A - R_B.
        """
        x = 10 ** (r / s)
        invx = 1.0 / x  # equals 10^(-r/s)
        return (x + 0.5 * kappa) / (invx + kappa + x)

    ratings: dict[str, float] = {}

    # Ensure every player has an entry.
    for a, b, sa in games:
        ratings.setdefault(a, float(base_rating))
        ratings.setdefault(b, float(base_rating))

    allowed = {0.0, 0.5, 1.0}

    for _ in range(iters):
        for a, b, sa in games:
            if sa not in allowed:
                raise ValueError(f"score must be one of {sorted(allowed)}; got {sa}")

            ra = ratings.get(a, float(base_rating))
            rb = ratings.get(b, float(base_rating))

            r = ra - rb
            ea = g(r)          # E[score_a_hat]
            eb = 1.0 - ea      # by symmetry g(-r) = 1 - g(r)

            sb = 1.0 - sa

            # Elo-Davidson update: R <- R + K*(observed_fractional - expected_fractional)
            ratings[a] = ra + K * (sa - ea)
            ratings[b] = rb + K * (sb - eb)

    return ratings

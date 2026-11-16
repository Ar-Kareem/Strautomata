
import time
from typing import List, Tuple, Optional, Dict

# 4x4 Tic Tac Toe: win by getting 4 in a row/col/diag.

N = 4
WIN_SCORE = 1_000_000

# Precompute all winning lines (as flat indices 0..15)
LINES = []
# Rows
for r in range(N):
    LINES.append([r * N + c for c in range(N)])
# Cols
for c in range(N):
    LINES.append([r * N + c for r in range(N)])
# Diagonals
LINES.append([i * N + i for i in range(N)])
LINES.append([i * N + (N - 1 - i) for i in range(N)])

# Cell -> list of line indices it belongs to (for faster heuristics)
CELL_TO_LINES = [[] for _ in range(N * N)]
for li, line in enumerate(LINES):
    for idx in line:
        CELL_TO_LINES[idx].append(li)

# Positional preference: favor center, then corners, then edges.
POS_WEIGHT = [0] * (N * N)
centers = {(1, 1), (1, 2), (2, 1), (2, 2)}
corners = {(0, 0), (0, 3), (3, 0), (3, 3)}
for r in range(N):
    for c in range(N):
        i = r * N + c
        if (r, c) in centers:
            POS_WEIGHT[i] = 6
        elif (r, c) in corners:
            POS_WEIGHT[i] = 4
        else:
            POS_WEIGHT[i] = 2


def _flatten(board: List[List[int]]) -> Tuple[int, ...]:
    return tuple(board[r][c] for r in range(N) for c in range(N))


def _unflatten_move(idx: int) -> Tuple[int, int]:
    return divmod(idx, N)


def _winner(state: Tuple[int, ...]) -> int:
    # Returns 1 if player 1 has 4-in-a-row, -1 if opponent does, else 0.
    for line in LINES:
        s = state[line[0]] + state[line[1]] + state[line[2]] + state[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _is_full(state: Tuple[int, ...]) -> bool:
    return 0 not in state


def _apply(state: Tuple[int, ...], idx: int, player: int) -> Tuple[int, ...]:
    # Create new state with move applied at idx.
    lst = list(state)
    lst[idx] = player
    return tuple(lst)


def _line_potential_score(own: int, opp: int) -> int:
    # For a line with own marks and opp marks (and remaining empties),
    # reward unblocked progress, penalize opponent progress.
    if own > 0 and opp > 0:
        return 0  # blocked line
    if own == 0 and opp == 0:
        return 1
    # Exponential growth to value 3-in-a-row threats heavily on 4x4.
    if opp == 0:
        # own in {1,2,3,4} (4 handled by terminal)
        return 10 ** own
    else:
        return -(10 ** opp)


def _static_eval(state: Tuple[int, ...]) -> int:
    # Evaluation from player 1's perspective (positive is good for player 1).
    w = _winner(state)
    if w == 1:
        return WIN_SCORE
    if w == -1:
        return -WIN_SCORE
    if _is_full(state):
        return 0

    score = 0

    # Line-based potential
    for line in LINES:
        own = opp = 0
        for idx in line:
            v = state[idx]
            if v == 1:
                own += 1
            elif v == -1:
                opp += 1
        score += _line_potential_score(own, opp)

    # Positional weights
    for i, v in enumerate(state):
        if v == 1:
            score += POS_WEIGHT[i]
        elif v == -1:
            score -= POS_WEIGHT[i]

    return score


def _immediate_winning_move(state: Tuple[int, ...], player: int) -> Optional[int]:
    for i, v in enumerate(state):
        if v == 0:
            ns = _apply(state, i, player)
            if _winner(ns) == player:
                return i
    return None


def _opponent_immediate_wins(state: Tuple[int, ...], player: int) -> set:
    # Returns set of indices that opponent could play now to win (must be blocked).
    opp = -player
    wins = set()
    for i, v in enumerate(state):
        if v == 0:
            ns = _apply(state, i, opp)
            if _winner(ns) == opp:
                wins.add(i)
    return wins


def _move_order(state: Tuple[int, ...], player: int) -> List[int]:
    empties = [i for i, v in enumerate(state) if v == 0]
    if not empties:
        return []

    # High-priority: winning moves, then blocks.
    win_idx = _immediate_winning_move(state, player)
    if win_idx is not None:
        return [win_idx]

    must_block = _opponent_immediate_wins(state, player)

    # Score moves for ordering to improve alpha-beta pruning.
    def key(i: int) -> int:
        # Blocking gets a big boost.
        block_bonus = 500_000 if i in must_block else 0

        # Small lookahead: immediate heuristic delta
        before = _static_eval(state)
        after = _static_eval(_apply(state, i, player))
        delta = after - before

        # Positional preference baked in via eval, but add explicit bias.
        pos = POS_WEIGHT[i] * 5

        return block_bonus + delta + pos

    empties.sort(key=key, reverse=True)

    # If there are must-block moves, consider them first (still ordered among themselves).
    if must_block:
        blocks = [i for i in empties if i in must_block]
        others = [i for i in empties if i not in must_block]
        return blocks + others

    return empties


def _negamax(
    state: Tuple[int, ...],
    depth: int,
    alpha: int,
    beta: int,
    player: int,
    ply: int,
    t_end: float,
    tt: Dict[Tuple[Tuple[int, ...], int, int], int],
) -> int:
    # Time check
    if time.perf_counter() >= t_end:
        raise TimeoutError

    w = _winner(state)
    if w != 0:
        # Prefer faster wins / slower losses
        return (WIN_SCORE - ply) if w == player else (-WIN_SCORE + ply)
    if depth == 0 or _is_full(state):
        # Convert static eval (player1 perspective) to current-player perspective
        return player * _static_eval(state)

    key = (state, player, depth)
    if key in tt:
        return tt[key]

    best = -10**18

    moves = _move_order(state, player)
    if not moves:
        return 0

    for m in moves:
        child = _apply(state, m, player)
        val = -_negamax(child, depth - 1, -beta, -alpha, -player, ply + 1, t_end, tt)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    state = _flatten(board)

    # Always return a legal move, even in degenerate inputs.
    empties = [i for i, v in enumerate(state) if v == 0]
    if not empties:
        return (0, 0)

    # Immediate win
    wmove = _immediate_winning_move(state, 1)
    if wmove is not None:
        return _unflatten_move(wmove)

    # Immediate block
    must_block = _opponent_immediate_wins(state, 1)
    if must_block:
        # Choose best block by ordering heuristic
        ordered = _move_order(state, 1)
        for m in ordered:
            if m in must_block:
                return _unflatten_move(m)
        # Fallback
        return _unflatten_move(next(iter(must_block)))

    # Iterative deepening negamax with alpha-beta and TT.
    t0 = time.perf_counter()
    t_end = t0 + 0.90  # leave headroom for Python overhead

    tt: Dict[Tuple[Tuple[int, ...], int, int], int] = {}

    best_move = None
    best_val = -10**18

    # Good default ordering baseline for root
    root_moves = _move_order(state, 1)
    best_move = root_moves[0]

    max_depth = len(empties)
    # Depth cap to stay safe; iterative deepening will stop earlier if needed.
    # On 4x4, searching quite deep is often feasible with pruning + TT.
    depth_cap = min(max_depth, 16)

    try:
        for depth in range(1, depth_cap + 1):
            if time.perf_counter() >= t_end:
                break

            cur_best_move = best_move
            cur_best_val = -10**18
            alpha = -10**18
            beta = 10**18

            # Reorder root moves each iteration; keep previous best first.
            moves = _move_order(state, 1)
            if best_move in moves:
                moves.remove(best_move)
                moves = [best_move] + moves

            for m in moves:
                if time.perf_counter() >= t_end:
                    raise TimeoutError
                child = _apply(state, m, 1)
                val = -_negamax(child, depth - 1, -beta, -alpha, -1, 1, t_end, tt)
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best_move = m
                if val > alpha:
                    alpha = val

                # If we found a forced win at this depth, can stop early.
                if cur_best_val >= WIN_SCORE - 2:
                    break

            # Only commit if the depth finished
            best_move, best_val = cur_best_move, cur_best_val

            if best_val >= WIN_SCORE - 2:
                break

    except TimeoutError:
        pass

    # Ensure legal move
    if best_move is None or state[best_move] != 0:
        for i in empties:
            return _unflatten_move(i)

    return _unflatten_move(best_move)

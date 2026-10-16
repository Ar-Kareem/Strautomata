
import time
from typing import List, Tuple, Optional, Dict

# 4x4 Tic Tac Toe: win = 4 in a row (rows, cols, 2 diagonals)

N = 4
MATE = 10**9

# Precompute all winning lines (10 lines total on 4x4)
LINES = []
for r in range(N):
    LINES.append(tuple(r * N + c for c in range(N)))
for c in range(N):
    LINES.append(tuple(r * N + c for r in range(N)))
LINES.append(tuple(i * N + i for i in range(N)))
LINES.append(tuple(i * N + (N - 1 - i) for i in range(N)))

# Center-ish squares preference (used for ordering / tie-breaking)
CENTER_CELLS = [(1, 1), (1, 2), (2, 1), (2, 2)]
CENTER_IDX = set(r * N + c for r, c in CENTER_CELLS)

# Corners next
CORNERS_IDX = {0, N - 1, (N - 1) * N, N * N - 1}


class _Timeout(Exception):
    pass


def _utility_us(state: Tuple[int, ...]) -> Optional[int]:
    """Terminal utility from 'us' (player 1) perspective: +MATE, -MATE, or 0 draw.
    Returns None if non-terminal.
    """
    # Check wins
    for line in LINES:
        s = state[line[0]] + state[line[1]] + state[line[2]] + state[line[3]]
        if s == 4:
            return MATE
        if s == -4:
            return -MATE
    # Draw?
    if 0 not in state:
        return 0
    return None


def _heuristic_us(state: Tuple[int, ...]) -> int:
    """Heuristic from 'us' perspective (player 1)."""
    score = 0

    # Line scoring: only "open" lines matter.
    # Exponential weights to prefer making 3-in-a-row etc.
    # (4-in-a-row handled as terminal.)
    w = [0, 1, 12, 180, 0]  # for 0..4 marks in an open line
    for line in LINES:
        cnt1 = cntm1 = 0
        for idx in line:
            v = state[idx]
            if v == 1:
                cnt1 += 1
            elif v == -1:
                cntm1 += 1
        if cnt1 and cntm1:
            continue  # blocked line
        if cntm1 == 0 and cnt1 > 0:
            score += w[cnt1]
        elif cnt1 == 0 and cntm1 > 0:
            score -= w[cntm1]

    # Small positional preferences: center > corner > edge
    for i, v in enumerate(state):
        if v == 0:
            continue
        if i in CENTER_IDX:
            score += 2 * v
        elif i in CORNERS_IDX:
            score += 1 * v
        else:
            score += 0

    return score


def _apply_move(state: Tuple[int, ...], idx: int, player: int) -> Tuple[int, ...]:
    lst = list(state)
    lst[idx] = player
    return tuple(lst)


def _legal_moves(state: Tuple[int, ...]) -> List[int]:
    return [i for i, v in enumerate(state) if v == 0]


def _immediate_winning_move(state: Tuple[int, ...], player: int) -> Optional[int]:
    """Return an index that wins immediately for 'player' if available."""
    for idx in _legal_moves(state):
        nxt = _apply_move(state, idx, player)
        util = _utility_us(nxt)
        if util is None:
            continue
        # util is from us perspective; interpret for player:
        # if player==1, a win means util == +MATE; if player==-1, win means util == -MATE.
        if (player == 1 and util == MATE) or (player == -1 and util == -MATE):
            return idx
    return None


def _ordered_moves(state: Tuple[int, ...], player: int, tt_best: Optional[int]) -> List[int]:
    """Move ordering to improve alpha-beta pruning."""
    moves = _legal_moves(state)

    # If TT suggests a best move, try it first
    if tt_best is not None and tt_best in moves:
        moves.remove(tt_best)
        moves = [tt_best] + moves

    def key(idx: int) -> int:
        # Prefer immediate wins, then blocks, then center/corner, then heuristic delta.
        # We compute a lightweight score; higher is better.
        nxt = _apply_move(state, idx, player)

        util = _utility_us(nxt)
        if util is not None:
            # winning move for current player should be top-ranked
            if (player == 1 and util == MATE) or (player == -1 and util == -MATE):
                return 10**8
            # avoid self-losing moves if any (rare with correct terminal detection)
            if (player == 1 and util == -MATE) or (player == -1 and util == MATE):
                return -10**8

        # Blocking opponent's immediate win next turn is very important
        opp_win = _immediate_winning_move(nxt, -player)
        block_bonus = 0 if opp_win is None else -5000  # leaving an immediate win is bad

        pos_bonus = 0
        if idx in CENTER_IDX:
            pos_bonus += 30
        elif idx in CORNERS_IDX:
            pos_bonus += 15
        else:
            pos_bonus += 5

        # Heuristic delta from us perspective; flip by player so ordering matches negamax
        delta = (_heuristic_us(nxt) - _heuristic_us(state)) * player

        return block_bonus + pos_bonus + delta

    moves.sort(key=key, reverse=True)
    return moves


def _negamax(
    state: Tuple[int, ...],
    player: int,
    depth: int,
    alpha: int,
    beta: int,
    end_time: float,
    tt: Dict[Tuple[Tuple[int, ...], int], Tuple[int, int, Optional[int]]],
) -> Tuple[int, Optional[int]]:
    """Return (value, best_move_idx) from current player's perspective (negamax).
    Value is from current-player viewpoint; caller at root uses player=1.
    """
    if time.perf_counter() >= end_time:
        raise _Timeout

    term = _utility_us(state)
    if term is not None:
        return term * player, None  # convert to current-player viewpoint
    if depth == 0:
        return _heuristic_us(state) * player, None

    key = (state, player)
    if key in tt:
        stored_depth, stored_val, stored_move = tt[key]
        if stored_depth >= depth:
            return stored_val, stored_move
        tt_best = stored_move
    else:
        tt_best = None

    best_val = -MATE
    best_move = None

    moves = _ordered_moves(state, player, tt_best)

    for idx in moves:
        nxt = _apply_move(state, idx, player)
        val, _ = _negamax(nxt, -player, depth - 1, -beta, -alpha, end_time, tt)
        val = -val
        if val > best_val:
            best_val = val
            best_move = idx
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    tt[key] = (depth, best_val, best_move)
    return best_val, best_move


def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to tuple state
    state = tuple(board[r][c] for r in range(N) for c in range(N))

    legal = _legal_moves(state)
    if not legal:
        # Game should be over; return something safe (arena typically won't call here).
        return (0, 0)

    # 1) Immediate win
    win_idx = _immediate_winning_move(state, player=1)
    if win_idx is not None:
        return divmod(win_idx, N)

    # 2) Immediate block
    block_idx = _immediate_winning_move(state, player=-1)
    if block_idx is not None:
        return divmod(block_idx, N)

    # 3) Iterative deepening alpha-beta with TT under time budget
    start = time.perf_counter()
    # Keep a margin for interpreter/overhead
    end_time = start + 0.95

    empties = len(legal)
    # In late game, try to solve exactly; otherwise search as deep as time allows.
    max_depth = empties  # full solve if possible within time via pruning/TT

    tt: Dict[Tuple[Tuple[int, ...], int], Tuple[int, int, Optional[int]]] = {}

    best_move_idx = None

    # Reasonable depth schedule: deepen gradually; on 4x4, this often reaches very deep.
    # Start at depth 2 to avoid purely heuristic one-ply blunders.
    for depth in range(2, max_depth + 1):
        try:
            val, mv = _negamax(state, player=1, depth=depth, alpha=-MATE, beta=MATE, end_time=end_time, tt=tt)
            if mv is not None:
                best_move_idx = mv
            # If proven mate, can stop early
            if val >= MATE // 2:
                break
        except _Timeout:
            break

    # Fallback if search couldn't set it (shouldn't happen)
    if best_move_idx is None:
        # Choose best heuristic move with safe ordering
        moves = _ordered_moves(state, player=1, tt_best=None)
        best_move_idx = moves[0] if moves else legal[0]

    r, c = divmod(best_move_idx, N)
    # Ensure legality
    if board[r][c] != 0:
        # last-resort: pick first legal
        idx = legal[0]
        r, c = divmod(idx, N)
    return (r, c)

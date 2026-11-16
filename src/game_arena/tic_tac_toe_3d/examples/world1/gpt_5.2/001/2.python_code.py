
import time
import random
from typing import List, Tuple, Optional, Dict, Any

# ---------- Precompute winning lines (49 total) ----------

def _generate_winning_lines() -> List[List[Tuple[int, int, int]]]:
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])  # along i
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])  # along j
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # along k

    # Face diagonals
    # Planes i = const (j-k diagonals)
    for i in range(3):
        lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
    # Planes j = const (i-k diagonals)
    for j in range(3):
        lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])
        lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])
    # Planes k = const (i-j diagonals)
    for k in range(3):
        lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
        lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])

    # Space diagonals (4)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

    return lines


WIN_LINES = _generate_winning_lines()


# ---------- Utilities: flattening, hashing, move gen ----------

def _flatten(board: List[List[List[int]]]) -> Tuple[int, ...]:
    # order: i, then j, then k
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


# Zobrist hashing for speed in transposition table
_rng = random.Random(0xC0FFEE)
_ZOBRIST = [[_rng.getrandbits(64) for _ in range(2)] for __ in range(27)]  # [cell][player_index]
# player_index: 0 for -1, 1 for +1

def _zobrist_hash(flat: Tuple[int, ...]) -> int:
    h = 0
    for p, v in enumerate(flat):
        if v == 0:
            continue
        h ^= _ZOBRIST[p][0 if v == -1 else 1]
    return h


def _legal_moves(flat: Tuple[int, ...]) -> List[int]:
    return [p for p, v in enumerate(flat) if v == 0]


def _apply(flat: Tuple[int, ...], pos: int, player: int) -> Tuple[int, ...]:
    lst = list(flat)
    lst[pos] = player
    return tuple(lst)


def _pos_to_coord(pos: int) -> Tuple[int, int, int]:
    i = pos // 9
    r = pos % 9
    j = r // 3
    k = r % 3
    return (i, j, k)


# ---------- Win / terminal detection ----------

def _winner(flat: Tuple[int, ...]) -> int:
    # returns 1 if player 1 wins, -1 if player -1 wins, else 0
    for line in WIN_LINES:
        s = 0
        for (i, j, k) in line:
            s += flat[_idx(i, j, k)]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _is_full(flat: Tuple[int, ...]) -> bool:
    return all(v != 0 for v in flat)


# ---------- Heuristic evaluation ----------

# positional weights: center > corners > edges
_POS_W = [0] * 27
for i in range(3):
    for j in range(3):
        for k in range(3):
            pos = _idx(i, j, k)
            # Manhattan distance to center (1,1,1)
            d = abs(i - 1) + abs(j - 1) + abs(k - 1)
            # d=0 center, d=1 face-centers, d=2 edge-centers, d=3 corners
            if d == 0:
                w = 8
            elif d == 1:
                w = 4
            elif d == 2:
                w = 2
            else:
                w = 3  # corners are strategically valuable
            _POS_W[pos] = w

# line scoring table
# open 1-in-line: small; open 2-in-line: big (threat); 3 is handled as terminal
_LINE_SCORE = {0: 0, 1: 2, 2: 30}

INF = 10**9
WIN_SCORE = 10**7  # must dominate any heuristic sum


def _evaluate(flat: Tuple[int, ...], player: int) -> int:
    # Positive means good for "player"
    w = _winner(flat)
    if w == player:
        return WIN_SCORE
    if w == -player:
        return -WIN_SCORE
    if _is_full(flat):
        return 0

    score = 0

    # positional bias
    for p, v in enumerate(flat):
        if v == player:
            score += _POS_W[p]
        elif v == -player:
            score -= _POS_W[p]

    # line potential
    for line in WIN_LINES:
        cnt_p = 0
        cnt_o = 0
        for (i, j, k) in line:
            v = flat[_idx(i, j, k)]
            if v == player:
                cnt_p += 1
            elif v == -player:
                cnt_o += 1

        if cnt_p and cnt_o:
            continue  # blocked line
        if cnt_p:
            score += _LINE_SCORE[cnt_p]
        elif cnt_o:
            score -= _LINE_SCORE[cnt_o]

    return score


# ---------- Search (iterative deepening alpha-beta negamax) ----------

class _TimeUp(Exception):
    pass


_TTABLE: Dict[Tuple[int, int, int], Tuple[int, Optional[int]]] = {}
# key: (hash, player, depth) -> (value, bestmove_pos)


def _ordered_moves(flat: Tuple[int, ...], player: int, moves: List[int]) -> List[int]:
    # order by tactical priority + static estimate after move
    # (wins first, then blocks, then heuristic)
    opp = -player
    scored = []
    for m in moves:
        nxt = _apply(flat, m, player)
        if _winner(nxt) == player:
            scored.append((10**9, m))
            continue

        # if opponent would win immediately after we don't play here, we already handle
        # immediate blocks outside; still useful in ordering:
        # check if placing here prevents an opp win on this same square is not meaningful,
        # but we can still prefer moves that create strong threats.
        h = _evaluate(nxt, player)

        # small extra: prefer center/corner structure
        h += _POS_W[m] * 2

        scored.append((h, m))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]


def _negamax(
    flat: Tuple[int, ...],
    player: int,
    depth: int,
    alpha: int,
    beta: int,
    zh: int,
    deadline: float,
) -> Tuple[int, Optional[int]]:
    if time.perf_counter() >= deadline:
        raise _TimeUp

    w = _winner(flat)
    if w != 0:
        return (WIN_SCORE if w == player else -WIN_SCORE, None)
    if depth == 0 or _is_full(flat):
        return (_evaluate(flat, player), None)

    key = (zh, player, depth)
    if key in _TTABLE:
        return _TTABLE[key]

    moves = _legal_moves(flat)
    if not moves:
        return (0, None)

    moves = _ordered_moves(flat, player, moves)

    best_val = -INF
    best_move = moves[0]

    # Alpha-beta negamax
    for m in moves:
        nxt = _apply(flat, m, player)
        nxt_hash = zh ^ _ZOBRIST[m][0 if player == -1 else 1]
        val, _ = _negamax(nxt, -player, depth - 1, -beta, -alpha, nxt_hash, deadline)
        val = -val

        if val > best_val:
            best_val = val
            best_move = m

        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    _TTABLE[key] = (best_val, best_move)
    return best_val, best_move


def _find_immediate(flat: Tuple[int, ...], player: int) -> Optional[int]:
    # returns winning move if exists
    for m in _legal_moves(flat):
        if _winner(_apply(flat, m, player)) == player:
            return m
    return None


def _find_block(flat: Tuple[int, ...], player: int) -> Optional[int]:
    # returns move that blocks opponent immediate win if exists
    opp = -player
    for m in _legal_moves(flat):
        if _winner(_apply(flat, m, opp)) == opp:
            return m
    return None


# ---------- Required API ----------

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    flat = _flatten(board)
    moves = _legal_moves(flat)
    if not moves:
        return (0, 0, 0)  # should never happen in valid play

    # 1) immediate win
    win_move = _find_immediate(flat, 1)
    if win_move is not None:
        return _pos_to_coord(win_move)

    # 2) immediate block
    block_move = _find_block(flat, 1)
    if block_move is not None:
        return _pos_to_coord(block_move)

    # 3) iterative deepening alpha-beta
    start = time.perf_counter()
    deadline = start + 0.95

    zh = _zobrist_hash(flat)

    # Fallback: best static move (always legal)
    ordered = _ordered_moves(flat, 1, moves)
    best_move = ordered[0]

    # Clear table occasionally to avoid unbounded growth across calls
    # (arena typically calls policy many times)
    if len(_TTABLE) > 200000:
        _TTABLE.clear()

    max_depth = min(12, len(moves))  # depth cap
    for depth in range(2, max_depth + 1):
        try:
            val, mv = _negamax(flat, 1, depth, -INF, INF, zh, deadline)
            if mv is not None:
                best_move = mv
            # If we find a forced win, no need to deepen.
            if val >= WIN_SCORE:
                break
        except _TimeUp:
            break

    # Ensure legality
    if flat[best_move] != 0:
        # extremely defensive fallback
        for m in moves:
            if flat[m] == 0:
                best_move = m
                break

    return _pos_to_coord(best_move)

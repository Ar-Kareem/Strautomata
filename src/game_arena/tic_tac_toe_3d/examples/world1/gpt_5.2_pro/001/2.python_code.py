
import time
from typing import List, Tuple, Optional, Dict

# 3x3x3 TicTacToe policy: returns (i,j,k) move for player "1".
# Board uses: 0 empty, 1 us, -1 opponent.

MATE = 10**9
TIME_BUDGET = 0.93  # seconds; keep margin under 1s

# ----------------------------
# Precompute lines (49 total)
# ----------------------------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k

def _coords(index: int) -> Tuple[int, int, int]:
    i = index // 9
    r = index % 9
    j = r // 3
    k = r % 3
    return i, j, k

def _generate_lines() -> List[List[int]]:
    lines = []

    # Along x (i)
    for j in range(3):
        for k in range(3):
            lines.append([_idx(i, j, k) for i in range(3)])

    # Along y (j)
    for i in range(3):
        for k in range(3):
            lines.append([_idx(i, j, k) for j in range(3)])

    # Along z (k)
    for i in range(3):
        for j in range(3):
            lines.append([_idx(i, j, k) for k in range(3)])

    # Diagonals in xy planes (fixed k)
    for k in range(3):
        lines.append([_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)])
        lines.append([_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)])

    # Diagonals in xz planes (fixed j)
    for j in range(3):
        lines.append([_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)])
        lines.append([_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)])

    # Diagonals in yz planes (fixed i)
    for i in range(3):
        lines.append([_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)])
        lines.append([_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)])

    # Space diagonals (4)
    lines.append([_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)])
    lines.append([_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)])
    lines.append([_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)])
    lines.append([_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)])

    # Sanity: should be 49
    return lines

LINES: List[List[int]] = _generate_lines()

# For quick checks: which lines go through a cell
LINES_THROUGH: List[List[int]] = [[] for _ in range(27)]
for li, line in enumerate(LINES):
    for pos in line:
        LINES_THROUGH[pos].append(li)

# ----------------------------
# Positional weights
# ----------------------------

def _pos_weight(index: int) -> int:
    i, j, k = _coords(index)
    center_count = (1 if i == 1 else 0) + (1 if j == 1 else 0) + (1 if k == 1 else 0)
    # center_count: 0 corner, 1 edge-center, 2 face-center, 3 cube-center
    if center_count == 3:
        return 6  # (1,1,1)
    if center_count == 0:
        return 4  # corners
    if center_count == 1:
        return 3  # edge-centers
    if center_count == 2:
        return 2  # face-centers
    return 1

POS_W = [_pos_weight(i) for i in range(27)]

# ----------------------------
# Zobrist hashing
# ----------------------------

def _splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = x
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    z = z ^ (z >> 31)
    return z & 0xFFFFFFFFFFFFFFFF

ZOBRIST = [[0, 0] for _ in range(27)]  # [idx][0 for +1, 1 for -1]
_seed = 0xC0FFEE123456789
for p in range(27):
    _seed = _splitmix64(_seed)
    ZOBRIST[p][0] = _seed
    _seed = _splitmix64(_seed)
    ZOBRIST[p][1] = _seed

def _hash_board(flat: List[int]) -> int:
    h = 0
    for idx, v in enumerate(flat):
        if v == 1:
            h ^= ZOBRIST[idx][0]
        elif v == -1:
            h ^= ZOBRIST[idx][1]
    return h

# ----------------------------
# Core helpers
# ----------------------------

def _is_win_after(flat: List[int], last_move: int, who: int) -> bool:
    # Check only lines through last_move.
    target = 3 * who
    for li in LINES_THROUGH[last_move]:
        s = flat[LINES[li][0]] + flat[LINES[li][1]] + flat[LINES[li][2]]
        if s == target:
            return True
    return False

def _line_sums(flat: List[int]) -> List[int]:
    return [flat[a] + flat[b] + flat[c] for (a, b, c) in LINES]  # type: ignore[misc]

def _evaluate_advantage_for_player1(flat: List[int]) -> int:
    # Positive means good for player +1.
    # Line-based scoring: open two-in-a-row is huge.
    sums = _line_sums(flat)
    score = 0

    # Weights tuned for 3-in-a-row game.
    for s in sums:
        if s == 3:
            score += 200000
        elif s == -3:
            score -= 200000
        elif s == 2:
            score += 700
        elif s == -2:
            score -= 700
        elif s == 1:
            score += 35
        elif s == -1:
            score -= 35
        # s==0: either empty or blocked; treat as neutral

    # Positional nudges
    # (kept small vs line values, but helps openings)
    for idx, v in enumerate(flat):
        if v == 1:
            score += POS_W[idx] * 6
        elif v == -1:
            score -= POS_W[idx] * 6

    return score

def _ordered_moves(flat: List[int], player: int, cap: Optional[int] = None) -> List[int]:
    empties = [i for i, v in enumerate(flat) if v == 0]
    if not empties:
        return []

    sums = _line_sums(flat)

    def mv_score(idx: int) -> int:
        sc = POS_W[idx] * 10
        win_hits = 0
        block_hits = 0
        make_threats = 0

        for li in LINES_THROUGH[idx]:
            s = sums[li]
            # With line sum s (from actual pieces), classify relative to current player
            if s == 2 * player:
                win_hits += 1      # placing here completes 3
            elif s == -2 * player:
                block_hits += 1    # prevents opponent 3
            elif s == 1 * player:
                make_threats += 1  # creates 2-in-row threat

        sc += win_hits * 1000000
        sc += block_hits * 250000
        sc += make_threats * 2500

        # Slight preference for moves that touch many lines (center does)
        sc += len(LINES_THROUGH[idx]) * 15
        return sc

    empties.sort(key=mv_score, reverse=True)
    if cap is not None and len(empties) > cap:
        return empties[:cap]
    return empties

# ----------------------------
# Negamax with alpha-beta + TT
# ----------------------------

class _Timeout(Exception):
    pass

class _TTEntry:
    __slots__ = ("depth", "value", "flag")
    def __init__(self, depth: int, value: int, flag: int):
        self.depth = depth
        self.value = value
        self.flag = flag  # 0 exact, 1 lowerbound, 2 upperbound

def _negamax(
    flat: List[int],
    player: int,
    depth: int,
    alpha: int,
    beta: int,
    last_move: Optional[int],
    ply: int,
    h: int,
    tt: Dict[Tuple[int, int], _TTEntry],
    t0: float,
    tmax: float,
) -> int:
    if time.perf_counter() - t0 > tmax:
        raise _Timeout

    # Terminal check: if opponent (who made last move) has won, we lose.
    if last_move is not None and _is_win_after(flat, last_move, -player):
        # Prefer slower losses (slightly)
        return -MATE + ply

    # Draw
    if all(v != 0 for v in flat):
        return 0

    if depth <= 0:
        return player * _evaluate_advantage_for_player1(flat)

    key = (h, player)
    entry = tt.get(key)
    if entry is not None and entry.depth >= depth:
        if entry.flag == 0:
            return entry.value
        elif entry.flag == 1:
            alpha = max(alpha, entry.value)
        else:
            beta = min(beta, entry.value)
        if alpha >= beta:
            return entry.value

    alpha0 = alpha
    beta0 = beta

    # Move ordering and light branching cap to fit time.
    # Early game: cap more; later: allow more exactness.
    empties_count = sum(1 for v in flat if v == 0)
    if empties_count >= 18:
        cap = 14
    elif empties_count >= 12:
        cap = 18
    else:
        cap = None

    moves = _ordered_moves(flat, player, cap=cap)

    best = -MATE
    for mv in moves:
        # Play move
        flat[mv] = player
        h2 = h ^ (ZOBRIST[mv][0] if player == 1 else ZOBRIST[mv][1])

        # If we win immediately, return mate (faster win is better)
        if _is_win_after(flat, mv, player):
            val = MATE - ply
        else:
            val = -_negamax(flat, -player, depth - 1, -beta, -alpha, mv, ply + 1, h2, tt, t0, tmax)

        # Undo
        flat[mv] = 0

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    # Store TT entry
    flag = 0
    if best <= alpha0:
        flag = 2  # upperbound
    elif best >= beta0:
        flag = 1  # lowerbound
    else:
        flag = 0  # exact
    prev = tt.get(key)
    if prev is None or depth >= prev.depth:
        tt[key] = _TTEntry(depth, best, flag)

    return best

def _find_immediate_move(flat: List[int], who: int) -> Optional[int]:
    # Return a move index that wins immediately for 'who', if exists.
    empties = [i for i, v in enumerate(flat) if v == 0]
    for mv in empties:
        flat[mv] = who
        won = _is_win_after(flat, mv, who)
        flat[mv] = 0
        if won:
            return mv
    return None

# ----------------------------
# Required API
# ----------------------------

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Flatten board
    flat = [0] * 27
    for i in range(3):
        for j in range(3):
            for k in range(3):
                flat[_idx(i, j, k)] = board[i][j][k]

    empties = [idx for idx, v in enumerate(flat) if v == 0]
    if not empties:
        # Should not happen in valid play; fallback.
        return (0, 0, 0)

    # 1) Immediate win
    mv = _find_immediate_move(flat, 1)
    if mv is not None:
        return _coords(mv)

    # 2) Immediate block
    mv = _find_immediate_move(flat, -1)
    if mv is not None:
        return _coords(mv)

    # 3) Search (iterative deepening)
    t0 = time.perf_counter()
    h = _hash_board(flat)
    tt: Dict[Tuple[int, int], _TTEntry] = {}

    # Default best: best ordered move
    root_moves = _ordered_moves(flat, 1, cap=None)
    best_move = root_moves[0]

    # Iteratively deepen until time runs out.
    # Depth limit: in practice this reaches ~5-8 within budget depending on position.
    max_depth = min(10, len(empties))  # avoid pointless deeper than remaining moves
    last_completed_depth = 0

    for depth in range(1, max_depth + 1):
        if time.perf_counter() - t0 > TIME_BUDGET:
            break
        try:
            # Root search with move-by-move to retain best_move even if timeout mid-depth.
            alpha = -MATE
            beta = MATE
            best_val = -MATE

            # Slight cap at root in very early game to keep within time.
            cap = 18 if len(empties) >= 20 else None
            moves = _ordered_moves(flat, 1, cap=cap)

            for mv in moves:
                if time.perf_counter() - t0 > TIME_BUDGET:
                    raise _Timeout

                flat[mv] = 1
                h2 = h ^ ZOBRIST[mv][0]

                if _is_win_after(flat, mv, 1):
                    val = MATE
                else:
                    val = -_negamax(flat, -1, depth - 1, -beta, -alpha, mv, 1, h2, tt, t0, TIME_BUDGET)

                flat[mv] = 0

                if val > best_val:
                    best_val = val
                    best_move = mv
                if best_val > alpha:
                    alpha = best_val
                if alpha >= beta:
                    break

            last_completed_depth = depth

        except _Timeout:
            break

    # Ensure legality
    if flat[best_move] != 0:
        # Fallback: pick first empty
        best_move = next((i for i in range(27) if flat[i] == 0), empties[0])

    return _coords(best_move)


import time
from typing import List, Tuple, Optional, Dict

N = 4
WIN_SUM = 4  # 4 in a row on 4x4

# Precompute all winning lines (rows, cols, diagonals)
LINES = []
# rows
for r in range(N):
    LINES.append([(r, c) for c in range(N)])
# cols
for c in range(N):
    LINES.append([(r, c) for r in range(N)])
# diagonals (main, anti)
LINES.append([(i, i) for i in range(N)])
LINES.append([(i, N - 1 - i) for i in range(N)])


def _flatten(board: List[List[int]]) -> Tuple[int, ...]:
    return tuple(board[r][c] for r in range(N) for c in range(N))


def _unflatten(b: Tuple[int, ...]) -> List[List[int]]:
    return [list(b[r * N:(r + 1) * N]) for r in range(N)]


def _winner(b: Tuple[int, ...]) -> int:
    # returns 1 if X (us) has won, -1 if opponent has won, 0 otherwise
    # Works for any position; checks full lines
    for line in LINES:
        s = 0
        for (r, c) in line:
            s += b[r * N + c]
        if s == WIN_SUM:
            return 1
        if s == -WIN_SUM:
            return -1
    return 0


def _legal_moves(b: Tuple[int, ...]) -> List[int]:
    return [i for i, v in enumerate(b) if v == 0]


def _move_order_score(idx: int) -> int:
    # Prefer central squares, then corners, then edges
    r, c = divmod(idx, N)
    # Manhattan distance to nearest center among 4 centers
    centers = [(1, 1), (1, 2), (2, 1), (2, 2)]
    dist = min(abs(r - cr) + abs(c - cc) for cr, cc in centers)
    # corners bonus
    is_corner = (r in (0, N - 1) and c in (0, N - 1))
    # edge (non-corner)
    is_edge = (r in (0, N - 1) or c in (0, N - 1)) and not is_corner
    # Lower dist is better; corners next; edges last
    score = 100 - 10 * dist
    if is_corner:
        score += 5
    elif is_edge:
        score -= 2
    return score


def _evaluate(b: Tuple[int, ...]) -> int:
    """
    Heuristic: sum line potentials.
    Lines with both players are dead (0).
    Otherwise exponential weight by count in line.
    """
    w = _winner(b)
    if w == 1:
        return 10_000_000
    if w == -1:
        return -10_000_000

    score = 0
    for line in LINES:
        my = 0
        opp = 0
        for (r, c) in line:
            v = b[r * N + c]
            if v == 1:
                my += 1
            elif v == -1:
                opp += 1
        if my and opp:
            continue
        if my:
            # Strongly prefer building 3-in-a-row threats etc.
            score += 10 ** my
        elif opp:
            score -= 10 ** opp

    # Mild preference for having more marks (tempo/initiative proxy)
    # (kept small so it doesn't override tactics)
    score += 2 * sum(1 for v in b if v == 1)
    score -= 2 * sum(1 for v in b if v == -1)
    return score


class TTEntry:
    __slots__ = ("depth", "value", "flag", "best_move")
    # flag: 0 exact, -1 upperbound, 1 lowerbound
    def __init__(self, depth: int, value: int, flag: int, best_move: Optional[int]):
        self.depth = depth
        self.value = value
        self.flag = flag
        self.best_move = best_move


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns a legal (row, col) move for player 1 on a 4x4 TicTacToe board.
    """
    start = time.perf_counter()
    time_limit = 0.92  # keep margin under 1s

    b0 = _flatten(board)
    empties = _legal_moves(b0)
    if not empties:
        # Shouldn't happen in normal play, but must return something.
        return (0, 0)

    # 1) Immediate win
    for m in empties:
        b = list(b0)
        b[m] = 1
        if _winner(tuple(b)) == 1:
            return divmod(m, N)

    # 2) Immediate block
    for m in empties:
        b = list(b0)
        b[m] = -1
        if _winner(tuple(b)) == -1:
            return divmod(m, N)

    # Transposition table
    tt: Dict[Tuple[Tuple[int, ...], int], TTEntry] = {}

    def negamax(b: Tuple[int, ...], player: int, depth: int, alpha: int, beta: int, ply: int) -> Tuple[int, Optional[int]]:
        # Time check
        if time.perf_counter() - start > time_limit:
            raise TimeoutError

        w = _winner(b)
        if w != 0:
            # prefer faster wins / slower losses
            # from perspective of "player" at this node:
            val = 10_000_000 - 1000 * ply
            return (val if w == player else -val), None

        moves = _legal_moves(b)
        if not moves:
            return 0, None  # draw

        if depth == 0:
            val = _evaluate(b)
            return (val if player == 1 else -val), None

        key = (b, player)
        entry = tt.get(key)
        if entry is not None and entry.depth >= depth:
            if entry.flag == 0:
                return entry.value, entry.best_move
            elif entry.flag == 1:  # lowerbound
                alpha = max(alpha, entry.value)
            else:  # upperbound
                beta = min(beta, entry.value)
            if alpha >= beta:
                return entry.value, entry.best_move

        # Move ordering: try TT best move first, then heuristics, plus forcing moves.
        tt_best = entry.best_move if entry is not None else None

        def ordered_moves():
            scored = []
            for m in moves:
                b2 = list(b)
                b2[m] = player
                b2t = tuple(b2)
                w2 = _winner(b2t)
                force = 0
                if w2 == player:
                    force = 10_000  # winning move
                else:
                    # detect if move creates immediate opponent win threat? (soft)
                    force = 0
                base = _move_order_score(m)
                scored.append((force + base, m))
            scored.sort(reverse=True)
            if tt_best is not None and tt_best in moves:
                # stable: ensure tt_best is first
                scored = [(s, m) for (s, m) in scored if m != tt_best]
                scored.insert(0, (999_999, tt_best))
            return [m for _, m in scored]

        best_val = -10**18
        best_move = None
        orig_alpha = alpha

        for m in ordered_moves():
            b2 = list(b)
            b2[m] = player
            b2t = tuple(b2)

            child_val, _ = negamax(b2t, -player, depth - 1, -beta, -alpha, ply + 1)
            val = -child_val

            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # Store in TT
        flag = 0
        if best_val <= orig_alpha:
            flag = -1  # upperbound
        elif best_val >= beta:
            flag = 1   # lowerbound
        tt[key] = TTEntry(depth, best_val, flag, best_move)
        return best_val, best_move

    # Iterative deepening
    best_move = None
    # Reasonable max depth: up to remaining empties
    max_depth = len(empties)

    # Aspiration window can speed things up, but keep simple and robust.
    try:
        for d in range(1, max_depth + 1):
            val, mv = negamax(b0, 1, d, -10**18, 10**18, 0)
            if mv is not None:
                best_move = mv
            # If we found a forced win, can stop early.
            if val >= 9_000_000:
                break
    except TimeoutError:
        pass

    if best_move is None:
        # Fallback: pick best heuristic move among legal
        # (still must be legal)
        best_score = -10**18
        for m in empties:
            b = list(b0)
            b[m] = 1
            sc = _evaluate(tuple(b)) + _move_order_score(m)
            if sc > best_score:
                best_score = sc
                best_move = m

    r, c = divmod(best_move, N)
    # Safety: ensure legal
    if board[r][c] != 0:
        # pick first empty as last resort
        for m in empties:
            rr, cc = divmod(m, N)
            if board[rr][cc] == 0:
                return (rr, cc)
        return (0, 0)
    return (r, c)

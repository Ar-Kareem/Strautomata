
import time
import random
from typing import List, Tuple, Optional, Set, Dict

Move = Tuple[int, int, int]

WIN_SCORE = 1_000_000
INF = 10**9
TIME_BUDGET = 0.93

# ---------- Precomputation ----------

def _build_lines():
    lines: List[Tuple[Move, Move, Move]] = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append(((0, j, k), (1, j, k), (2, j, k)))
    for i in range(3):
        for k in range(3):
            lines.append(((i, 0, k), (i, 1, k), (i, 2, k)))
    for i in range(3):
        for j in range(3):
            lines.append(((i, j, 0), (i, j, 1), (i, j, 2)))

    # Plane diagonals
    for k in range(3):  # xy planes
        lines.append(((0, 0, k), (1, 1, k), (2, 2, k)))
        lines.append(((0, 2, k), (1, 1, k), (2, 0, k)))
    for j in range(3):  # xz planes
        lines.append(((0, j, 0), (1, j, 1), (2, j, 2)))
        lines.append(((0, j, 2), (1, j, 1), (2, j, 0)))
    for i in range(3):  # yz planes
        lines.append(((i, 0, 0), (i, 1, 1), (i, 2, 2)))
        lines.append(((i, 0, 2), (i, 1, 1), (i, 2, 0)))

    # Space diagonals
    lines.append(((0, 0, 0), (1, 1, 1), (2, 2, 2)))
    lines.append(((0, 0, 2), (1, 1, 1), (2, 2, 0)))
    lines.append(((0, 2, 0), (1, 1, 1), (2, 0, 2)))
    lines.append(((0, 2, 2), (1, 1, 1), (2, 0, 0)))

    return lines


LINES = _build_lines()
CELLS: List[Move] = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]
CELL_TO_LINES: List[List[List[List[int]]]] = [[[[] for _ in range(3)] for _ in range(3)] for _ in range(3)]

for idx, line in enumerate(LINES):
    for i, j, k in line:
        CELL_TO_LINES[i][j][k].append(idx)

CELL_WEIGHT = [[[len(CELL_TO_LINES[i][j][k]) for k in range(3)] for j in range(3)] for i in range(3)]

_LINE_VALUE = [0, 5, 45, WIN_SCORE]

_rng = random.Random(1337)
ZOBRIST = [[_rng.getrandbits(64) for _ in range(2)] for _ in range(27)]


def _index(move: Move) -> int:
    i, j, k = move
    return i * 9 + j * 3 + k


class SearchTimeout(Exception):
    pass


# ---------- Basic board utilities ----------

def _legal_moves(board: List[List[List[int]]]) -> List[Move]:
    return [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]


def _has_winner(board: List[List[List[int]]]) -> int:
    for line in LINES:
        (a1, b1, c1), (a2, b2, c2), (a3, b3, c3) = line
        v = board[a1][b1][c1]
        if v != 0 and v == board[a2][b2][c2] == board[a3][b3][c3]:
            return v
    return 0


def _move_wins(board: List[List[List[int]]], move: Move, player: int) -> bool:
    i, j, k = move
    for li in CELL_TO_LINES[i][j][k]:
        line = LINES[li]
        good = True
        for a, b, c in line:
            if board[a][b][c] != player:
                good = False
                break
        if good:
            return True
    return False


def _winning_moves(board: List[List[List[int]]], player: int) -> Set[Move]:
    wins: Set[Move] = set()
    for line in LINES:
        p = 0
        o = 0
        empty = None
        for a, b, c in line:
            v = board[a][b][c]
            if v == player:
                p += 1
            elif v == -player:
                o += 1
            else:
                empty = (a, b, c)
        if p == 2 and o == 0 and empty is not None:
            wins.add(empty)
    return wins


def _fork_moves(board: List[List[List[int]]], player: int, moves: Optional[List[Move]] = None) -> List[Move]:
    if moves is None:
        moves = _legal_moves(board)
    forks: List[Move] = []
    for move in moves:
        i, j, k = move
        board[i][j][k] = player
        if not _move_wins(board, move, player):
            wm = _winning_moves(board, player)
            if len(wm) >= 2:
                forks.append(move)
        board[i][j][k] = 0
    forks.sort(key=lambda m: (CELL_WEIGHT[m[0]][m[1]][m[2]], m == (1, 1, 1)), reverse=True)
    return forks


def _board_hash(board: List[List[List[int]]]) -> int:
    h = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                if v == 1:
                    h ^= ZOBRIST[_index((i, j, k))][0]
                elif v == -1:
                    h ^= ZOBRIST[_index((i, j, k))][1]
    return h


# ---------- Evaluation and ordering ----------

def _evaluate_fixed(board: List[List[List[int]]]) -> int:
    score = 0

    # Positional value: cells that lie on more winning lines are more valuable
    pos = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                if v != 0:
                    pos += v * CELL_WEIGHT[i][j][k]
    score += 3 * pos

    my_threats: Set[Move] = set()
    opp_threats: Set[Move] = set()

    for line in LINES:
        c1 = 0
        c2 = 0
        empty = None
        for a, b, c in line:
            v = board[a][b][c]
            if v == 1:
                c1 += 1
            elif v == -1:
                c2 += 1
            else:
                empty = (a, b, c)

        if c1 and c2:
            continue
        if c1:
            score += _LINE_VALUE[c1]
            if c1 == 2 and empty is not None:
                my_threats.add(empty)
        elif c2:
            score -= _LINE_VALUE[c2]
            if c2 == 2 and empty is not None:
                opp_threats.add(empty)

    score += 120 * len(my_threats)
    score -= 135 * len(opp_threats)

    if len(my_threats) >= 2:
        score += 250
    if len(opp_threats) >= 2:
        score -= 280

    return score


def _move_order_score(
    board: List[List[List[int]]],
    move: Move,
    player: int,
    urgent: Optional[Set[Move]] = None,
    tt_best: Optional[Move] = None,
) -> int:
    i, j, k = move
    score = CELL_WEIGHT[i][j][k] * 10

    if move == (1, 1, 1):
        score += 30
    if urgent is not None and move in urgent:
        score += 2000
    if tt_best is not None and move == tt_best:
        score += 2_000_000

    for li in CELL_TO_LINES[i][j][k]:
        same = 0
        other = 0
        for a, b, c in LINES[li]:
            if (a, b, c) == move:
                continue
            v = board[a][b][c]
            if v == player:
                same += 1
            elif v == -player:
                other += 1

        if other == 0:
            if same == 2:
                score += 100_000
            elif same == 1:
                score += 70
            else:
                score += 6

        if same == 0:
            if other == 2:
                score += 9_000
            elif other == 1:
                score += 24

    return score


def _ordered_moves(
    board: List[List[List[int]]],
    moves: List[Move],
    player: int,
    urgent: Optional[Set[Move]] = None,
    tt_best: Optional[Move] = None,
) -> List[Move]:
    scored = [(_move_order_score(board, m, player, urgent, tt_best), m) for m in moves]
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _candidate_limit(empties: int, root: bool) -> int:
    if root:
        if empties >= 23:
            return 12
        if empties >= 19:
            return 14
        if empties >= 15:
            return 16
        if empties >= 11:
            return 18
        return 27
    else:
        if empties >= 23:
            return 8
        if empties >= 19:
            return 10
        if empties >= 15:
            return 12
        if empties >= 11:
            return 16
        return 27


# ---------- Search ----------

def _search(
    board: List[List[List[int]]],
    to_move: int,
    depth: int,
    alpha: int,
    beta: int,
    empties: int,
    last_move: Optional[Move],
    deadline: float,
    h: int,
    tt: Dict[Tuple[int, int], Tuple[int, int, int, Optional[Move]]],
    nodes: List[int],
) -> int:
    nodes[0] += 1
    if (nodes[0] & 255) == 0 and time.perf_counter() >= deadline:
        raise SearchTimeout

    # Previous move may already have ended the game
    if last_move is not None and _move_wins(board, last_move, -to_move):
        return -WIN_SCORE - depth

    if empties == 0:
        return 0

    # Immediate tactical status for side to move
    my_wins = _winning_moves(board, to_move)
    if my_wins:
        return WIN_SCORE + depth

    opp_wins = _winning_moves(board, -to_move)
    if len(opp_wins) >= 2:
        return -WIN_SCORE - depth

    if depth == 0:
        return to_move * _evaluate_fixed(board)

    key = (h, to_move)
    entry = tt.get(key)
    tt_best = None
    alpha_orig = alpha
    if entry is not None:
        entry_depth, flag, val, best_move = entry
        tt_best = best_move
        if entry_depth >= depth:
            if flag == 0:  # exact
                return val
            elif flag == -1:  # upper
                beta = min(beta, val)
            else:  # lower
                alpha = max(alpha, val)
            if alpha >= beta:
                return val

    legal = _legal_moves(board)

    if len(opp_wins) == 1:
        moves = list(opp_wins)
        urgent = opp_wins
    else:
        moves = legal
        urgent = None

    ordered = _ordered_moves(board, moves, to_move, urgent=urgent, tt_best=tt_best)

    if len(opp_wins) == 0 and len(my_wins) == 0 and len(ordered) > 1:
        ordered = ordered[:_candidate_limit(empties, root=False)]

    best = -INF
    best_move = ordered[0] if ordered else None

    for move in ordered:
        i, j, k = move
        board[i][j][k] = to_move
        zh = ZOBRIST[_index(move)][0 if to_move == 1 else 1]
        val = -_search(
            board,
            -to_move,
            depth - 1,
            -beta,
            -alpha,
            empties - 1,
            move,
            deadline,
            h ^ zh,
            tt,
            nodes,
        )
        board[i][j][k] = 0

        if val > best:
            best = val
            best_move = move
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    flag = 0
    if best <= alpha_orig:
        flag = -1  # upper bound
    elif best >= beta:
        flag = 1   # lower bound
    tt[key] = (depth, flag, best, best_move)

    return best


def _root_search(
    board: List[List[List[int]]],
    candidates: List[Move],
    depth: int,
    deadline: float,
    h: int,
    tt: Dict[Tuple[int, int], Tuple[int, int, int, Optional[Move]]],
    urgent: Optional[Set[Move]] = None,
) -> Tuple[int, Move]:
    if time.perf_counter() >= deadline:
        raise SearchTimeout

    empties = len(_legal_moves(board))
    tt_entry = tt.get((h, 1))
    tt_best = tt_entry[3] if tt_entry is not None else None

    ordered = _ordered_moves(board, candidates, 1, urgent=urgent, tt_best=tt_best)

    if len(candidates) == empties and len(ordered) > 1:
        ordered = ordered[:_candidate_limit(empties, root=True)]

    best_move = ordered[0]
    best_val = -INF
    alpha = -INF
    beta = INF
    nodes = [0]

    for move in ordered:
        if time.perf_counter() >= deadline:
            raise SearchTimeout

        i, j, k = move
        board[i][j][k] = 1
        zh = ZOBRIST[_index(move)][0]
        val = -_search(
            board,
            -1,
            depth - 1,
            -beta,
            -alpha,
            empties - 1,
            move,
            deadline,
            h ^ zh,
            tt,
            nodes,
        )
        board[i][j][k] = 0

        if val > best_val:
            best_val = val
            best_move = move
        if val > alpha:
            alpha = val

    return best_val, best_move


# ---------- Public policy ----------

def policy(board: List[List[List[int]]]) -> Move:
    legal = _legal_moves(board)
    if not legal:
        return (0, 0, 0)

    # If somehow called on a terminal state, still return a legal move.
    if _has_winner(board) != 0:
        return legal[0]

    empties = len(legal)

    # Immediate win
    my_wins = _winning_moves(board, 1)
    if my_wins:
        return _ordered_moves(board, list(my_wins), 1)[0]

    # Immediate block(s)
    opp_wins = _winning_moves(board, -1)
    if len(opp_wins) == 1:
        return next(iter(opp_wins))

    # Strong opening rule: take center very early if available and no immediate tactic overrides it
    if board[1][1][1] == 0 and (27 - empties) <= 1:
        return (1, 1, 1)

    # Create a fork if possible
    if not opp_wins:
        my_forks = _fork_moves(board, 1, legal)
        if my_forks:
            return my_forks[0]

    urgent: Optional[Set[Move]] = None
    candidates = legal

    # If opponent has multiple immediate wins, we can only block one; search among those blocks.
    if opp_wins:
        candidates = list(opp_wins)
        urgent = opp_wins
    else:
        # If exactly one opponent fork exists, occupying it is usually safest.
        opp_forks = _fork_moves(board, -1, legal)
        if len(opp_forks) == 1:
            return opp_forks[0]
        if opp_forks:
            urgent = set(opp_forks)

    # Extra early-game center preference
    if board[1][1][1] == 0 and empties >= 24 and (1, 1, 1) in candidates:
        return (1, 1, 1)

    # Search
    h = _board_hash(board)
    tt: Dict[Tuple[int, int], Tuple[int, int, int, Optional[Move]]] = {}
    deadline = time.perf_counter() + TIME_BUDGET

    # Safe fallback
    ordered_fallback = _ordered_moves(board, candidates, 1, urgent=urgent)
    best_move = ordered_fallback[0] if ordered_fallback else legal[0]

    if len(candidates) == 1:
        return candidates[0]

    max_depth = min(empties, 10)
    for depth in range(1, max_depth + 1):
        try:
            val, move = _root_search(board, candidates, depth, deadline, h, tt, urgent=urgent)
            if move is not None:
                best_move = move
            if abs(val) >= WIN_SCORE // 2:
                break
        except SearchTimeout:
            break

    # Final legality guard
    i, j, k = best_move
    if 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3 and board[i][j][k] == 0:
        return best_move

    for mv in legal:
        a, b, c = mv
        if board[a][b][c] == 0:
            return mv

    return legal[0]

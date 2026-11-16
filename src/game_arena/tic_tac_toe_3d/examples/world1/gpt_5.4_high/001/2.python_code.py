
from typing import List, Tuple
import time


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


IDX_TO_COORD = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]


def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append((_idx(0, j, k), _idx(1, j, k), _idx(2, j, k)))  # along i
    for i in range(3):
        for k in range(3):
            lines.append((_idx(i, 0, k), _idx(i, 1, k), _idx(i, 2, k)))  # along j
    for i in range(3):
        for j in range(3):
            lines.append((_idx(i, j, 0), _idx(i, j, 1), _idx(i, j, 2)))  # along k

    # Plane diagonals
    for k in range(3):  # i-j planes
        lines.append((_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)))
        lines.append((_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)))
    for j in range(3):  # i-k planes
        lines.append((_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)))
        lines.append((_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)))
    for i in range(3):  # j-k planes
        lines.append((_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)))
        lines.append((_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)))

    # Space diagonals
    lines.append((_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)))
    lines.append((_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)))
    lines.append((_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)))
    lines.append((_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)))

    return lines


LINES = _generate_lines()
CELL_TO_LINES = [[] for _ in range(27)]
for lid, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(lid)

CELL_WEIGHTS = [len(x) for x in CELL_TO_LINES]
CENTER = _idx(1, 1, 1)
CORNERS = [_idx(i, j, k) for i in (0, 2) for j in (0, 2) for k in (0, 2)]

WIN_SCORE = 1_000_000
INF = 10 ** 9

TT = {}


try:
    (1).bit_count

    def _popcount(x: int) -> int:
        return x.bit_count()
except AttributeError:
    def _popcount(x: int) -> int:
        return bin(x).count("1")


class SearchTimeout(Exception):
    pass


def _flatten(board: List[List[List[int]]]) -> List[int]:
    return [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]


def _winner_abs(cells: List[int]) -> int:
    c = cells
    for a, b, d in LINES:
        s = c[a] + c[b] + c[d]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _winning_moves(cells: List[int], player: int, sort: bool = False) -> List[int]:
    c = cells
    target = 2 * player
    out = []
    seen_mask = 0

    for a, b, d in LINES:
        s = c[a] + c[b] + c[d]
        if s == target:
            if c[a] == 0:
                e = a
            elif c[b] == 0:
                e = b
            elif c[d] == 0:
                e = d
            else:
                continue
            bit = 1 << e
            if not (seen_mask & bit):
                seen_mask |= bit
                out.append(e)

    if sort and len(out) > 1:
        out.sort(key=lambda m: (CELL_WEIGHTS[m], m), reverse=True)
    return out


def _move_heuristic(cells: List[int], idx: int, player: int) -> int:
    c = cells
    score = CELL_WEIGHTS[idx] * 12
    if idx == CENTER:
        score += 20

    for lid in CELL_TO_LINES[idx]:
        a, b, d = LINES[lid]
        va, vb, vd = c[a], c[b], c[d]
        ours = (va == player) + (vb == player) + (vd == player)
        opp = (va == -player) + (vb == -player) + (vd == -player)

        if opp == 0:
            if ours == 2:
                score += 320
            elif ours == 1:
                score += 36

        if ours == 0:
            if opp == 2:
                score += 260
            elif opp == 1:
                score += 12

    return score


def _order_moves(cells: List[int], player: int, tt_move: int = None) -> List[int]:
    scored = []
    for idx, v in enumerate(cells):
        if v != 0:
            continue
        s = _move_heuristic(cells, idx, player)
        if tt_move is not None and idx == tt_move:
            s += 10_000
        scored.append((s, idx))
    scored.sort(reverse=True)
    return [idx for _, idx in scored]


def _abs_eval(cells: List[int]) -> int:
    c = cells
    score = 0
    our_threat_mask = 0
    opp_threat_mask = 0

    for a, b, d in LINES:
        va, vb, vd = c[a], c[b], c[d]
        ours = (va == 1) + (vb == 1) + (vd == 1)
        opp = (va == -1) + (vb == -1) + (vd == -1)

        if ours and opp:
            continue

        if ours:
            if ours == 1:
                score += 6
            elif ours == 2:
                score += 80
                if va == 0:
                    our_threat_mask |= 1 << a
                elif vb == 0:
                    our_threat_mask |= 1 << b
                else:
                    our_threat_mask |= 1 << d

        elif opp:
            if opp == 1:
                score -= 6
            elif opp == 2:
                score -= 90
                if va == 0:
                    opp_threat_mask |= 1 << a
                elif vb == 0:
                    opp_threat_mask |= 1 << b
                else:
                    opp_threat_mask |= 1 << d

    for idx, v in enumerate(c):
        if v != 0:
            score += v * CELL_WEIGHTS[idx] * 3

    score += 140 * _popcount(our_threat_mask)
    score -= 160 * _popcount(opp_threat_mask)
    return score


def _choose_best(cells: List[int], moves: List[int], player: int = 1) -> int:
    best = moves[0]
    best_score = -INF

    for m in moves:
        s = _move_heuristic(cells, m, player)
        cells[m] = player

        w = _winner_abs(cells)
        if w == player:
            s += WIN_SCORE // 2
        elif w == -player:
            s -= WIN_SCORE // 2
        else:
            my_wins = len(_winning_moves(cells, player, sort=False))
            opp_wins = len(_winning_moves(cells, -player, sort=False))
            s += 250 * my_wins
            s -= 5000 * opp_wins
            s += (player * _abs_eval(cells)) // 10

        cells[m] = 0

        if s > best_score:
            best_score = s
            best = m

    return best


def _depth_limit(empties: int) -> int:
    if empties >= 23:
        return 3
    if empties >= 17:
        return 4
    if empties >= 13:
        return 5
    if empties >= 10:
        return 6
    return empties


def _negamax(
    cells: List[int],
    player: int,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
    deadline: float,
) -> int:
    if time.perf_counter() >= deadline:
        raise SearchTimeout

    key = (tuple(cells), player)
    entry = TT.get(key)
    tt_move = entry[2] if entry is not None else None
    if entry is not None and entry[3] and entry[0] >= depth:
        return entry[1]

    w = _winner_abs(cells)
    if w != 0:
        abs_score = WIN_SCORE - ply
        return player * (abs_score if w == 1 else -abs_score)

    empties = 0
    for v in cells:
        if v == 0:
            empties += 1
    if empties == 0:
        return 0

    my_wins = _winning_moves(cells, player, sort=False)
    if my_wins:
        return WIN_SCORE - ply - 1

    opp_wins = _winning_moves(cells, -player, sort=False)
    if len(opp_wins) > 1:
        return -(WIN_SCORE - ply - 2)

    if depth == 0:
        return player * _abs_eval(cells)

    moves = _order_moves(cells, player, tt_move)

    if opp_wins:
        forced = set(opp_wins)
        filtered = [m for m in moves if m in forced]
        if filtered:
            moves = filtered

    best = -INF
    best_move = moves[0]
    exact = True

    for m in moves:
        cells[m] = player
        score = -_negamax(cells, -player, depth - 1, -beta, -alpha, ply + 1, deadline)
        cells[m] = 0

        if score > best:
            best = score
            best_move = m

        if best > alpha:
            alpha = best

        if alpha >= beta:
            exact = False
            break

    TT[key] = (depth, best, best_move, exact)
    return best


def _search_root(cells: List[int], depth: int, deadline: float) -> Tuple[int, int]:
    root_key = (tuple(cells), 1)
    entry = TT.get(root_key)
    tt_move = entry[2] if entry is not None else None

    moves = _order_moves(cells, 1, tt_move)
    opp_wins = _winning_moves(cells, -1, sort=False)
    if opp_wins:
        forced = set(opp_wins)
        filtered = [m for m in moves if m in forced]
        if filtered:
            moves = filtered

    best = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF

    for m in moves:
        if time.perf_counter() >= deadline:
            raise SearchTimeout

        cells[m] = 1
        score = -_negamax(cells, -1, depth - 1, -beta, -alpha, 1, deadline)
        cells[m] = 0

        if score > best:
            best = score
            best_move = m

        if best > alpha:
            alpha = best

        if best >= WIN_SCORE - 100:
            break

    TT[root_key] = (depth, best, best_move, True)
    return best, best_move


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    cells = _flatten(board)
    legal = [i for i, v in enumerate(cells) if v == 0]

    if not legal:
        return (0, 0, 0)

    # If given a terminal/invalid board, still return a legal move.
    if _winner_abs(cells) != 0:
        return IDX_TO_COORD[legal[0]]

    moves_played = 27 - len(legal)

    # Opening
    if moves_played == 0:
        return IDX_TO_COORD[CENTER]

    # Immediate win
    wins = _winning_moves(cells, 1, sort=True)
    if wins:
        return IDX_TO_COORD[_choose_best(cells, wins, 1)]

    # Immediate block
    opp_wins = _winning_moves(cells, -1, sort=True)
    if opp_wins:
        return IDX_TO_COORD[_choose_best(cells, opp_wins, 1)]

    # Early opening choices
    if moves_played == 1:
        if cells[CENTER] == 0:
            return IDX_TO_COORD[CENTER]
        corner_moves = [c for c in CORNERS if cells[c] == 0]
        if corner_moves:
            return IDX_TO_COORD[_choose_best(cells, corner_moves, 1)]

    # Safe fork creation
    safe_forks = []
    for m in legal:
        cells[m] = 1
        if _winner_abs(cells) != 1:
            if not _winning_moves(cells, -1, sort=False):
                if len(_winning_moves(cells, 1, sort=False)) >= 2:
                    safe_forks.append(m)
        cells[m] = 0

    if safe_forks:
        return IDX_TO_COORD[_choose_best(cells, safe_forks, 1)]

    # If center is still free very early, take it.
    if cells[CENTER] == 0 and moves_played <= 3:
        return IDX_TO_COORD[CENTER]

    # Search
    TT.clear()
    best_move = _choose_best(cells, legal, 1)
    deadline = time.perf_counter() + 0.88
    max_depth = _depth_limit(len(legal))

    for depth in range(1, max_depth + 1):
        try:
            score, move = _search_root(cells, depth, deadline)
            if move is not None and cells[move] == 0:
                best_move = move
            if abs(score) >= WIN_SCORE - 100:
                break
        except SearchTimeout:
            break

    if best_move not in legal:
        best_move = legal[0]

    return IDX_TO_COORD[best_move]

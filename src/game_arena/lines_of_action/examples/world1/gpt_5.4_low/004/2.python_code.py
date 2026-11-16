
import time
from math import inf

# 8 directions
DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

WIN_SCORE = 10**7
TIME_LIMIT = 0.92


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def board_key(board):
    return tuple(tuple(row) for row in board)


def count_lines(board):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag1 = {}  # r-c
    diag2 = {}  # r+c
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag1[r - c] = diag1.get(r - c, 0) + 1
                diag2[r + c] = diag2.get(r + c, 0) + 1
    return row_counts, col_counts, diag1, diag2


def line_length(row_counts, col_counts, diag1, diag2, r, c, dr, dc):
    if dr == 0:
        return row_counts[r]
    if dc == 0:
        return col_counts[c]
    if dr == dc:
        return diag1[r - c]
    return diag2[r + c]


def generate_moves(board):
    """
    Generates legal moves for current player = 1.
    Returns list of moves as tuples:
    (fr, fc, tr, tc, is_capture)
    """
    row_counts, col_counts, diag1, diag2 = count_lines(board)
    moves = []

    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue

            for dr, dc in DIRS:
                dist = line_length(row_counts, col_counts, diag1, diag2, r, c, dr, dc)
                tr = r + dr * dist
                tc = c + dc * dist
                if not in_bounds(tr, tc):
                    continue
                if board[tr][tc] == 1:
                    continue

                # Cannot jump over enemy pieces
                blocked = False
                for step in range(1, dist):
                    rr = r + dr * step
                    cc = c + dc * step
                    if board[rr][cc] == -1:
                        blocked = True
                        break
                if blocked:
                    continue

                moves.append((r, c, tr, tc, 1 if board[tr][tc] == -1 else 0))

    return moves


def apply_move(board, move):
    """
    Apply move for current player=1, then switch perspective
    so next player is again represented as 1.
    """
    fr, fc, tr, tc, _ = move
    newb = [row[:] for row in board]
    newb[fr][fc] = 0
    newb[tr][tc] = 1
    # switch perspective
    for r in range(8):
        row = newb[r]
        for c in range(8):
            row[c] = -row[c]
    return newb


def positions_of(board, player):
    out = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                out.append((r, c))
    return out


def component_info(board, player):
    pos = positions_of(board, player)
    if not pos:
        return 0, 0, 0.0

    seen = set()
    comps = 0
    largest = 0

    for start in pos:
        if start in seen:
            continue
        comps += 1
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc) and board[rr][cc] == player and (rr, cc) not in seen:
                    seen.add((rr, cc))
                    stack.append((rr, cc))
        if size > largest:
            largest = size

    # compactness: sum of squared distances to centroid
    n = len(pos)
    cr = sum(r for r, _ in pos) / n
    cc = sum(c for _, c in pos) / n
    spread = 0.0
    for r, c in pos:
        dr = r - cr
        dc = c - cc
        spread += dr * dr + dc * dc

    return comps, largest, spread


def is_connected(board, player):
    pos = positions_of(board, player)
    if len(pos) <= 1:
        return True
    seen = {pos[0]}
    stack = [pos[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == player and (rr, cc) not in seen:
                seen.add((rr, cc))
                stack.append((rr, cc))
    return len(seen) == len(pos)


def evaluate(board):
    # Terminal-like checks
    my_conn = is_connected(board, 1)
    opp_conn = is_connected(board, -1)
    if my_conn and opp_conn:
        return WIN_SCORE // 2
    if my_conn:
        return WIN_SCORE
    if opp_conn:
        return -WIN_SCORE

    my_comps, my_largest, my_spread = component_info(board, 1)
    opp_comps, opp_largest, opp_spread = component_info(board, -1)

    my_moves = len(generate_moves(board))

    # Opponent mobility: flip perspective cheaply
    flipped = [[-board[r][c] for c in range(8)] for r in range(8)]
    opp_moves = len(generate_moves(flipped))

    my_count = sum(1 for r in range(8) for c in range(8) if board[r][c] == 1)
    opp_count = sum(1 for r in range(8) for c in range(8) if board[r][c] == -1)

    score = 0
    score += 900 * (opp_comps - my_comps)
    score += 120 * (my_largest - opp_largest)
    score += 8 * (opp_spread - my_spread)
    score += 10 * (my_moves - opp_moves)
    score += 40 * (my_count - opp_count)

    return score


def move_heuristic(board, move):
    fr, fc, tr, tc, is_cap = move
    score = 0

    # Captures are often useful
    score += 300 * is_cap

    # Centralization
    before_center = abs(fr - 3.5) + abs(fc - 3.5)
    after_center = abs(tr - 3.5) + abs(tc - 3.5)
    score += int((before_center - after_center) * 10)

    # Prefer moves that reduce our components
    before_comps, _, before_spread = component_info(board, 1)
    newb = apply_move(board, move)
    # newb is opponent perspective, so our moved side is now -1 in newb
    after_comps, _, after_spread = component_info(newb, -1)
    score += 120 * (before_comps - after_comps)
    score += int(before_spread - after_spread)

    # Immediate win
    if is_connected(newb, -1):
        score += 1000000

    return score


def ordered_moves(board):
    moves = generate_moves(board)
    moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)
    return moves


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}

    def time_up(self):
        return time.time() >= self.deadline

    def negamax(self, board, depth, alpha, beta):
        if self.time_up():
            raise TimeoutError

        key = (board_key(board), depth)
        if key in self.tt:
            return self.tt[key]

        if is_connected(board, 1):
            return WIN_SCORE
        if is_connected(board, -1):
            return -WIN_SCORE
        if depth == 0:
            return evaluate(board)

        moves = ordered_moves(board)
        if not moves:
            # No legal moves: very bad
            return -WIN_SCORE // 2

        best = -inf
        for mv in moves:
            child = apply_move(board, mv)
            score = -self.negamax(child, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        self.tt[key] = best
        return best


def move_to_str(move):
    fr, fc, tr, tc, _ = move
    return f"{fr},{fc}:{tr},{tc}"


def policy(board) -> str:
    start = time.time()
    deadline = start + TIME_LIMIT

    moves = generate_moves(board)
    if not moves:
        # Should be rare/impossible in normal arena states.
        # Try to return something harmless-looking, but legal moves are expected to exist.
        return "0,0:0,0"

    # Legal fallback
    best_move = moves[0]

    # Quick ordering
    moves = ordered_moves(board)
    best_move = moves[0]

    searcher = Searcher(deadline)

    # Dynamic depth
    max_depth = 4 if len(moves) <= 10 else 3
    if len(moves) <= 5:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            if time.time() >= deadline:
                break

            local_best = best_move
            local_best_score = -inf
            alpha = -inf
            beta = inf

            root_moves = ordered_moves(board)

            for mv in root_moves:
                if time.time() >= deadline:
                    raise TimeoutError

                child = apply_move(board, mv)
                score = -searcher.negamax(child, depth - 1, -beta, -alpha)

                if score > local_best_score:
                    local_best_score = score
                    local_best = mv
                if score > alpha:
                    alpha = score

            best_move = local_best

    except TimeoutError:
        pass

    return move_to_str(best_move)


import time
import numpy as np

# Precompute lines and mapping for fast move generation
_LINES = []
_CELL_TO_LINES = {}

# rows
for r in range(8):
    line = [(r, c) for c in range(8)]
    _LINES.append(line)
# cols
for c in range(8):
    line = [(r, c) for r in range(8)]
    _LINES.append(line)
# main diagonals
for offset in range(-7, 8):
    line = [(r, r + offset) for r in range(8) if 0 <= r + offset < 8]
    if len(line) >= 2:
        _LINES.append(line)
# anti-diagonals
for offset in range(0, 15):
    line = [(r, offset - r) for r in range(8) if 0 <= offset - r < 8]
    if len(line) >= 2:
        _LINES.append(line)

for i, line in enumerate(_LINES):
    for rc in line:
        _CELL_TO_LINES.setdefault(rc, []).append(i)


def _count_components(board, player):
    """Return the number of 8-connected groups for the given player."""
    visited = set()
    components = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and (r, c) not in visited:
                components += 1
                stack = [(r, c)]
                visited.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if board[nr][nc] == player and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    stack.append((nr, nc))
    return components


def _evaluate(board):
    """Heuristic value from the perspective of player 1."""
    my_comp = _count_components(board, 1)
    opp_comp = _count_components(board, -1)

    # terminal check
    if my_comp == 1:
        return 100000
    if opp_comp == 1:
        return -100000

    my_pieces = sum(row.count(1) for row in board)
    opp_pieces = sum(row.count(-1) for row in board)

    # connectivity score: incentivise fewer components
    my_score = 10 * (my_pieces - my_comp)
    opp_score = 10 * (opp_pieces - opp_comp)
    piece_diff = 0.5 * (my_pieces - opp_pieces)
    return my_score - opp_score + piece_diff


def _get_moves(board, player):
    """Generate all legal moves for player."""
    moves = []
    opp = -player
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                rc = (r, c)
                for line_idx in _CELL_TO_LINES.get(rc, []):
                    line = _LINES[line_idx]
                    distance = sum(abs(board[rr][cc]) for (rr, cc) in line)
                    pos = line.index(rc)

                    # forward
                    dest_idx = pos + distance
                    if dest_idx < len(line):
                        dr, dc = line[dest_idx]
                        if board[dr][dc] != player:
                            blocked = False
                            for step in range(1, distance):
                                mr, mc = line[pos + step]
                                if board[mr][mc] == opp:
                                    blocked = True
                                    break
                            if not blocked:
                                moves.append((rc, (dr, dc)))

                    # backward
                    dest_idx = pos - distance
                    if dest_idx >= 0:
                        dr, dc = line[dest_idx]
                        if board[dr][dc] != player:
                            blocked = False
                            for step in range(1, distance):
                                mr, mc = line[pos - step]
                                if board[mr][mc] == opp:
                                    blocked = True
                                    break
                            if not blocked:
                                moves.append((rc, (dr, dc)))
    return moves


class _TimeOut(Exception):
    pass


def _negamax(board, depth, player, alpha, beta, start_time, time_limit):
    """Negamax with alpha-beta pruning."""
    if time.perf_counter() - start_time > time_limit:
        raise _TimeOut

    opp = -player
    if _count_components(board, opp) == 1:
        return -100000 - depth  # prefer earlier losses for opponent
    if depth == 0:
        return player * _evaluate(board)

    moves = _get_moves(board, player)
    if not moves:
        return -10000  # no moves, treat as loss

    # simple move ordering: captures first
    moves.sort(key=lambda m: 1 if board[m[1][0]][m[1][1]] == opp else 0, reverse=True)

    best = -float('inf')
    for (fr, fc), (tr, tc) in moves:
        piece = board[fr][fc]
        captured = board[tr][tc]

        board[fr][fc] = 0
        board[tr][tc] = piece

        val = -_negamax(board, depth - 1, opp, -beta, -alpha, start_time, time_limit)

        board[fr][fc] = piece
        board[tr][tc] = captured

        if val > best:
            best = val
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best


def policy(board):
    """Return the best move string."""
    # Convert board to list of lists if needed
    if isinstance(board, np.ndarray):
        board = board.tolist()
    else:
        board = [list(row) for row in board]

    player = 1
    start_time = time.perf_counter()
    time_limit = 0.90  # seconds

    best_move = None
    depth = 1

    # Get all legal moves
    moves = _get_moves(board, player)
    if not moves:
        return ""  # Should never happen in a real game

    # Initial ordering
    moves.sort(key=lambda m: 1 if board[m[1][0]][m[1][1]] == -player else 0, reverse=True)
    best_move = moves[0]

    while True:
        if time.perf_counter() - start_time > time_limit:
            break
        try:
            alpha = -float('inf')
            beta = float('inf')
            best_val = -float('inf')
            current_best = moves[0]

            for move in moves:
                (fr, fc), (tr, tc) = move
                piece = board[fr][fc]
                captured = board[tr][tc]

                board[fr][fc] = 0
                board[tr][tc] = piece

                val = -_negamax(board, depth - 1, -player, -beta, -alpha, start_time, time_limit)

                board[fr][fc] = piece
                board[tr][tc] = captured

                if val > best_val:
                    best_val = val
                    current_best = move
                alpha = max(alpha, val)
                if alpha >= beta:
                    break

            best_move = current_best
            depth += 1
            if best_val > 90000:  # win found
                break
        except _TimeOut:
            break

    (fr, fc), (tr, tc) = best_move
    return f"{fr},{fc}:{tr},{tc}"

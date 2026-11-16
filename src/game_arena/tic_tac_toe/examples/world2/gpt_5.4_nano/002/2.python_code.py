
import random
import math
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Player is 1, opponent is -1. Empty is 0.
    n = 4
    me = 1
    opp = -1

    # Check win for given player
    def winner(b, player: int) -> bool:
        lines = []
        # rows
        for r in range(n):
            lines.append(b[r])
        # cols
        for c in range(n):
            lines.append([b[r][c] for r in range(n)])
        # diags
        lines.append([b[i][i] for i in range(n)])
        lines.append([b[i][n-1-i] for i in range(n)])
        # 4-in-a-row needed (since 4x4)
        target = [player]*n
        for line in lines:
            if line == target:
                return True
        return False

    def board_full(b) -> bool:
        for r in range(n):
            for c in range(n):
                if b[r][c] == 0:
                    return False
        return True

    def get_moves(b):
        moves = []
        for r in range(n):
            for c in range(n):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    # Heuristic evaluation: count strong lines potential.
    def evaluate(b) -> int:
        # If terminal, return big values
        if winner(b, me):
            return 10**9
        if winner(b, opp):
            return -10**9
        if board_full(b):
            return 0

        # Lines: rows, cols, diags
        lines = []
        for r in range(n):
            lines.append([(r, c) for c in range(n)])
        for c in range(n):
            lines.append([(r, c) for r in range(n)])
        lines.append([(i, i) for i in range(n)])
        lines.append([(i, n-1-i) for i in range(n)])

        def line_score(cells):
            s = 0
            mine = 0
            theirs = 0
            empty = 0
            for (r, c) in cells:
                v = b[r][c]
                if v == me:
                    mine += 1
                elif v == opp:
                    theirs += 1
                else:
                    empty += 1
            # If line blocked by opponent marks, it can only contribute if theirs==0
            if theirs > 0 and mine > 0:
                return 0
            # Pure mine potential
            if theirs == 0 and mine > 0:
                # More of our marks => better; use exponential-ish weighting
                # 1 -> 2, 2 -> 10, 3 -> 50
                if mine == 1:
                    s += 2
                elif mine == 2:
                    s += 10
                elif mine == 3:
                    s += 50
                else:  # mine==4 handled as terminal
                    s += 1000
            # Pure opponent threat: penalize similarly
            if mine == 0 and theirs > 0:
                if theirs == 1:
                    s -= 2
                elif theirs == 2:
                    s -= 10
                elif theirs == 3:
                    s -= 50
                else:
                    s -= 1000
            return s

        total = 0
        for cells in lines:
            total += line_score(cells)
        return total

    # Minimax with alpha-beta. Depth tuned for 4x4.
    # Use iterative deepening with time guard.
    import time
    start_time = time.time()
    time_limit = 0.95  # keep under 1s

    # For speed, represent board as list of lists; copy locally when needed.
    def minimax(b, depth, alpha, beta, maximizing: bool):
        # Terminal or depth limit
        if winner(b, me):
            return 10**9 + depth
        if winner(b, opp):
            return -10**9 - depth
        if depth == 0 or board_full(b):
            return evaluate(b)

        moves = get_moves(b)

        # Move ordering: prefer center-ish and moves that create/stop threats.
        # Simple ordering by immediate local heuristic
        def move_order_key(m):
            r, c = m
            # prefer central cells
            center_dist = abs(r - 1.5) + abs(c - 1.5)
            # also prefer moves that increase evaluation immediately for maximizing
            b2 = [row[:] for row in b]
            b2[r][c] = me if maximizing else opp
            h = evaluate(b2)
            # For maximizing: higher h first; for minimizing: lower h first
            # Use sign to unify
            return (center_dist, -h if maximizing else h)

        moves.sort(key=move_order_key)

        if maximizing:
            best = -math.inf
            for (r, c) in moves:
                b2 = [row[:] for row in b]
                b2[r][c] = me
                val = minimax(b2, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
                if time.time() - start_time > time_limit:
                    # return current best if time is almost up
                    return best
            return best
        else:
            best = math.inf
            for (r, c) in moves:
                b2 = [row[:] for row in b]
                b2[r][c] = opp
                val = minimax(b2, depth - 1, alpha, beta, True)
                if val < best:
                    best = val
                beta = min(beta, val)
                if beta <= alpha:
                    break
                if time.time() - start_time > time_limit:
                    return best
            return best

    # Make a working copy
    b0 = [row[:] for row in board]

    # 1) Immediate winning move
    for (r, c) in get_moves(b0):
        b1 = [row[:] for row in b0]
        b1[r][c] = me
        if winner(b1, me):
            return (r, c)

    # 2) Immediate blocking move (prevent opponent win)
    for (r, c) in get_moves(b0):
        b1 = [row[:] for row in b0]
        b1[r][c] = opp
        if winner(b1, opp):
            return (r, c)

    # 3) Minimax search
    moves = get_moves(b0)
    # If no moves (shouldn't happen), return (0,0) though it may be illegal; but game should not be over.
    if not moves:
        return (0, 0)

    # Depth selection: adapt to remaining empties
    empties = len(moves)
    if empties >= 10:
        depth = 3
    elif empties >= 6:
        depth = 4
    else:
        depth = 5

    best_move = moves[0]
    best_val = -math.inf

    # Try iterative deepening for better quality within time
    # Cap at depth computed above
    max_depth = depth
    for d in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break
        current_best_move = best_move
        current_best_val = -math.inf

        for (r, c) in moves:
            if time.time() - start_time > time_limit:
                break
            b1 = [row[:] for row in b0]
            b1[r][c] = me
            val = minimax(b1, d - 1, -math.inf, math.inf, False)
            if val > current_best_val:
                current_best_val = val
                current_best_move = (r, c)

        if current_best_val > best_val:
            best_val = current_best_val
            best_move = current_best_move

    return best_move

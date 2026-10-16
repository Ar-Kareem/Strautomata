
from __future__ import annotations
from functools import lru_cache
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    4x4 Tic Tac Toe:
      0 empty, 1 us, -1 opponent.
    Returns (row, col) where board[row][col] == 0.
    """
    N = 4
    K = 4  # need 4 in a row to win on 4x4

    # Gather empty cells
    empties = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]

    # Quick sanity: if no moves, return something legal (shouldn't happen)
    if not empties:
        return (0, 0)

    # Precompute all winning lines (rows, cols, diags)
    lines = []
    # rows
    for r in range(N):
        lines.append([(r, c) for c in range(N)])
    # cols
    for c in range(N):
        lines.append([(r, c) for r in range(N)])
    # main diagonals (top-left to bottom-right, only length 4)
    lines.append([(i, i) for i in range(N)])
    # anti-diagonal
    lines.append([(i, N - 1 - i) for i in range(N)])

    def winner_state(b) -> int:
        """Return 1 if we win, -1 if opponent wins, 0 otherwise."""
        for line in lines:
            vals = [b[r][c] for r, c in line]
            s = sum(vals)
            # Since cells are in {1,-1,0} and need all 4, sum is 4 or -4.
            if s == 4:
                return 1
            if s == -4:
                return -1
        return 0

    def full(b) -> bool:
        for r in range(N):
            for c in range(N):
                if b[r][c] == 0:
                    return False
        return True

    # Tactical immediate win/block checks to avoid search overhead
    # 1) Can we win in one move?
    for r, c in empties:
        b2 = [row[:] for row in board]
        b2[r][c] = 1
        if winner_state(b2) == 1:
            return (r, c)

    # 2) Must we block opponent immediate win?
    for r, c in empties:
        b2 = [row[:] for row in board]
        b2[r][c] = -1
        if winner_state(b2) == -1:
            return (r, c)

    # Encode board into an integer key for caching
    # Use base-3 encoding for 16 cells: 0 empty, 1 us, 2 opponent
    # mapping: -1 -> 2
    def key_of(b) -> int:
        k = 0
        p = 1
        for r in range(N):
            for c in range(N):
                v = b[r][c]
                if v == 0:
                    digit = 0
                elif v == 1:
                    digit = 1
                else:
                    digit = 2
                k += digit * p
                p *= 3
        return k

    # Move ordering heuristic: prefer center and cells participating in more lines
    center_priority = {(1, 1): 0, (1, 2): 0, (2, 1): 0, (2, 2): 0,
                       (0, 0): 1, (0, 3): 1, (3, 0): 1, (3, 3): 1,
                       (0, 1): 2, (0, 2): 2, (1, 0): 2, (2, 0): 2,
                       (1, 3): 2, (2, 3): 2, (3, 1): 2, (3, 2): 2}
    # line participation count for each cell
    cell_lines = [[0]*N for _ in range(N)]
    for line in lines:
        for r, c in line:
            cell_lines[r][c] += 1

    # Depth limit fallback (early game): full search can be large, so we cap in empties > 10
    # We'll still include tactical checks at each node.
    max_depth = 10 if len(empties) > 10 else 16

    # Heuristic evaluation for non-terminal states (used only at depth limit)
    # Score: count potential lines with no opponent pieces for our turns, and vice versa.
    def heuristic(b) -> int:
        # large weights for near-complete lines
        score = 0
        for line in lines:
            vals = [b[r][c] for r, c in line]
            if -1 in vals and 1 in vals:
                continue
            cnt1 = sum(1 for v in vals if v == 1)
            cntm1 = sum(1 for v in vals if v == -1)
            if cntm1 == 0 and cnt1 > 0:
                # our line
                if cnt1 == 3:
                    score += 50
                elif cnt1 == 2:
                    score += 10
                else:
                    score += 3
            elif cnt1 == 0 and cntm1 > 0:
                # opponent line
                if cntm1 == 3:
                    score -= 50
                elif cntm1 == 2:
                    score -= 10
                else:
                    score -= 3
        return score

    @lru_cache(maxsize=None)
    def minimax(state_key: int, turn: int, depth: int, alpha: int, beta: int) -> int:
        # NOTE: alpha/beta shouldn't be in cache key in standard form due to dependence,
        # but Python's lru_cache requires hashable args. To keep correctness,
        # we won't cache alpha/beta: instead we cache only state/turn/depth.
        # Therefore we split cache properly below.

        raise RuntimeError("Should not be called")

    cache = {}

    def minimax2(b, turn: int, depth: int, alpha: int, beta: int) -> int:
        # turn: 1 means we to move, -1 means opponent to move
        state_key = key_of(b)
        ckey = (state_key, turn, depth)
        if ckey in cache:
            return cache[ckey]

        w = winner_state(b)
        if w != 0:
            # If w is winner for player 1, map to perspective of current player?
            # We want score from our perspective: winning for us => +inf, for opponent => -inf
            res = 1000000 if w == 1 else -1000000
            cache[ckey] = res
            return res
        if full(b):
            cache[ckey] = 0
            return 0
        if depth == 0:
            res = heuristic(b)
            cache[ckey] = res
            return res

        # Generate moves (ordered)
        moves = [(r, c) for r in range(N) for c in range(N) if b[r][c] == 0]
        # order: higher cell_lines and center priority
        def order_key(m):
            r, c = m
            return (cell_lines[r][c], -center_priority.get((r, c), 3), - (abs(r-1.5)+abs(c-1.5)))
        moves.sort(key=order_key, reverse=True)

        best = -10**9 if turn == 1 else 10**9

        # Additional tactical pruning at node: immediate win/block for side to move
        # If side to move can win now, return immediately.
        for r, c in moves:
            b2 = [row[:] for row in b]
            b2[r][c] = turn
            if winner_state(b2) == turn:
                res = 1000000 if turn == 1 else -1000000
                cache[ckey] = res
                return res

        for r, c in moves:
            b2 = [row[:] for row in b]
            b2[r][c] = turn
            val = minimax2(b2, -turn, depth - 1, alpha, beta)
            if turn == 1:
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            else:
                if val < best:
                    best = val
                beta = min(beta, best)
                if beta <= alpha:
                    break

        cache[ckey] = best
        return best

    # Choose best move from current position for us (turn=1)
    board0 = [row[:] for row in board]

    # Depth selection: if late game, search deeper (full possible up to 16).
    # We'll set depth based on remaining empties.
    empties_count = len(empties)
    depth = max_depth
    if empties_count <= 8:
        depth = 16
    elif empties_count <= 10:
        depth = 14
    elif empties_count <= 12:
        depth = 12

    best_move = empties[0]
    best_val = -10**9

    # Order top-level moves
    moves = empties[:]
    def top_order_key(m):
        r, c = m
        return (cell_lines[r][c], -center_priority.get((r, c), 3), - (abs(r-1.5)+abs(c-1.5)))
    moves.sort(key=top_order_key, reverse=True)

    alpha = -10**9
    beta = 10**9

    for r, c in moves:
        b2 = [row[:] for row in board0]
        b2[r][c] = 1
        val = minimax2(b2, -1, depth - 1, alpha, beta)
        if val > best_val:
            best_val = val
            best_move = (r, c)
        alpha = max(alpha, best_val)
        # can't alpha-beta prune at top too much, but it's okay

    return best_move

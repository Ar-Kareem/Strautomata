
import math
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe (win = 4 in a row). Board values:
      0 empty, 1 self, -1 opponent.
    Returns (row, col) with an empty cell.
    """
    n = 4
    # Precompute all length-4 lines in 4x4: 4 rows, 4 cols, 2 diagonals
    lines = []
    # rows
    for r in range(n):
        lines.append([(r, c) for c in range(n)])
    # cols
    for c in range(n):
        lines.append([(r, c) for r in range(n)])
    # main diagonals
    lines.append([(i, i) for i in range(n)])
    lines.append([(i, n - 1 - i) for i in range(n)])

    empties = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 0]
    if not empties:
        # Shouldn't happen (must be legal), but return something deterministic.
        return (0, 0)

    # Helper: check for winner
    def winner(b):
        for ln in lines:
            s = 0
            for r, c in ln:
                s += b[r][c]
            if s == 4:
                return 1
            if s == -4:
                return -1
        return 0

    # Helper: check if move is legal
    def is_empty(b, r, c):
        return b[r][c] == 0

    # Immediate win/block
    me = 1
    opp = -1
    w = winner(board)
    if w != 0:
        # Game already decided; choose any empty (for safety)
        return empties[0]

    def apply_move(b, r, c, player):
        nb = [row[:] for row in b]
        nb[r][c] = player
        return nb

    # Generate move order heuristic (center-first)
    center_weights = [[3, 2, 2, 3],
                       [2, 1, 1, 2],
                       [2, 1, 1, 2],
                       [3, 2, 2, 3]]
    def move_key(move):
        r, c = move
        # Higher weight first
        return -center_weights[r][c]

    # Immediate winning move
    for r, c in sorted(empties, key=move_key):
        nb = apply_move(board, r, c, me)
        if winner(nb) == me:
            return (r, c)

    # Immediate block opponent win
    for r, c in sorted(empties, key=move_key):
        nb = apply_move(board, r, c, opp)
        if winner(nb) == opp:
            return (r, c)

    # Evaluation function
    # For each line of 4:
    # - If both players present => 0 for that line
    # - If only me present: score increases with number of me and openness
    # - If only opp present: subtract similarly
    # Also add a small preference for occupying central cells.
    def evaluate(b):
        # Terminal check
        w = winner(b)
        if w == me:
            return 10_000_000
        if w == opp:
            return -10_000_000

        score = 0
        for ln in lines:
            vals = [b[r][c] for r, c in ln]
            has_me = me in vals
            has_opp = opp in vals
            if has_me and has_opp:
                continue
            count_me = vals.count(me)
            count_opp = vals.count(opp)
            count_empty = vals.count(0)

            # Score "open" lines more; closed lines can't happen in 4-in-row,
            # but empties are what remain.
            if has_me:
                # count_me: 1..3; count_empty: 3..1
                # Stronger as count_me increases.
                if count_me == 1:
                    score += 30
                elif count_me == 2:
                    score += 250
                elif count_me == 3:
                    score += 2500
                else:
                    # count_me==4 handled by terminal
                    score += 0
                # Slightly encourage keeping lines open (more empties)
                score += count_empty
            elif has_opp:
                if count_opp == 1:
                    score -= 30
                elif count_opp == 2:
                    score -= 250
                elif count_opp == 3:
                    score -= 2500
                else:
                    score -= 0
                score -= count_empty

        # Center preference
        for r in range(n):
            for c in range(n):
                if b[r][c] == me:
                    score += 2 * center_weights[r][c]
                elif b[r][c] == opp:
                    score -= 2 * center_weights[r][c]
        return score

    # Minimax with alpha-beta, depth-limited and with memoization
    def board_to_key(b, turn):
        # Encode 4x4 in base-3 to keep memo size reasonable
        # mapping: -1 -> 0, 0 -> 1, 1 -> 2
        mapping = { -1: 0, 0: 1, 1: 2 }
        x = 0
        p = 1
        for r in range(n):
            for c in range(n):
                x += mapping[b[r][c]] * p
                p *= 3
        return (x, turn)

    # Choose depth based on remaining empties for performance
    # Typical: early game use moderate depth, late game deeper.
    remaining = len(empties)
    if remaining >= 12:
        max_depth = 3
    elif remaining >= 7:
        max_depth = 4
    else:
        max_depth = 6

    # Also limit branching by ordering; but don't prune moves illegally.
    # We'll consider top-K moves by heuristic when branching is huge.
    # In 4x4, branching isn't crazy; keep K adaptive.
    def top_moves(b, current_player):
        e = [(r, c) for r in range(n) for c in range(n) if b[r][c] == 0]
        scored = []
        for r, c in e:
            # Quick one-move threat heuristic
            nb = [row[:] for row in b]
            nb[r][c] = current_player
            # If that move wins, make it very high
            wb = winner(nb)
            if wb == current_player:
                h = 1e9
            elif wb == -current_player:
                h = 5e8  # shouldn't occur for current_player move usually, but keep
            else:
                # Use evaluation difference as a local heuristic (cheap)
                h = evaluate(nb)
            scored.append((h, (r, c)))
        scored.sort(reverse=True, key=lambda x: x[0])
        e_sorted = [m for _, m in scored]
        # Adaptive K
        K = 8 if len(e_sorted) > 10 else 12
        return e_sorted[:K]

    @lru_cache(maxsize=None)
    def minimax(key, depth, alpha, beta):
        # Not used; cache handled by board key within wrapper
        raise RuntimeError("minimax key wrapper not intended to be used directly")

    def alphabeta(b, depth, alpha, beta, turn):
        # turn: 1 for me, -1 for opp
        w = winner(b)
        if w == me:
            return 10_000_000
        if w == opp:
            return -10_000_000

        if depth == 0:
            return evaluate(b)

        # Memoization
        k = board_to_key(b, turn)
        # Can't safely store alpha/beta dependent results without careful bounds,
        # so we store only exact at leaf depths by using a standard trick:
        # We'll do memo only for depth and full bounds by storing best score.
        # Since we do alpha-beta, results are exact because we search to completion
        # for this node; so cache is valid for (k, depth, turn).
        cache_key = (k, depth, turn)
        if cache_key in memo:
            return memo[cache_key]

        best = -math.inf if turn == me else math.inf
        moves = top_moves(b, turn)
        for r, c in moves:
            nb = [row[:] for row in b]
            nb[r][c] = turn
            val = alphabeta(nb, depth - 1, alpha, beta, -turn)
            if turn == me:
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            else:
                if val < best:
                    best = val
                beta = min(beta, best)
                if alpha >= beta:
                    break

        memo[cache_key] = best
        return best

    memo = {}

    # Choose best move for me using search
    best_move = None
    best_val = -math.inf
    possible = sorted(empties, key=move_key)
    # Try immediate "threat moves" ordering by quick local eval
    # for better pruning.
    ordered = []
    for r, c in possible:
        nb = apply_move(board, r, c, me)
        ordered.append((evaluate(nb), (r, c)))
    ordered.sort(reverse=True, key=lambda x: x[0])

    # Consider up to top moves (adaptive)
    topK = 10 if len(ordered) > 12 else len(ordered)
    ordered_moves = [m for _, m in ordered[:topK]]

    alpha = -math.inf
    beta = math.inf
    for r, c in ordered_moves:
        nb = apply_move(board, r, c, me)
        val = alphabeta(nb, max_depth - 1, alpha, beta, opp)
        if val > best_val:
            best_val = val
            best_move = (r, c)
        alpha = max(alpha, best_val)

    # Fallback in case of unexpected issues
    if best_move is None:
        best_move = ordered_moves[0] if ordered_moves else empties[0]

    return best_move


import time
from collections import deque

# Directions: 8-connected movement
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

CENTER = 3.5


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def board_to_key(board):
    # Compact immutable key for transposition table
    return tuple(tuple(row) for row in board)


def count_pieces_line(board, r, c, dr, dc):
    """Count all pieces (both colors) on the full line of movement through (r,c)."""
    if dr == 0 and dc != 0:
        # Row
        return sum(1 for x in board[r] if x != 0)
    if dc == 0 and dr != 0:
        # Column
        return sum(1 for rr in range(8) if board[rr][c] != 0)

    # Diagonal (either kind). Walk to the start of the diagonal then traverse.
    rr, cc = r, c
    while in_bounds(rr - dr, cc - dc):
        rr -= dr
        cc -= dc
    cnt = 0
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    return cnt


def generate_moves(board):
    """Generate all legal moves for current player (pieces == 1)."""
    moves = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] != 1:
                continue
            for dr, dc in DIRS:
                n = count_pieces_line(board, r, c, dr, dc)
                tr, tc = r + dr * n, c + dc * n
                if not in_bounds(tr, tc):
                    continue
                # Destination cannot be occupied by friendly piece
                if board[tr][tc] == 1:
                    continue
                # Cannot jump over enemy pieces
                blocked = False
                for step in range(1, n):
                    rr, cc = r + dr * step, c + dc * step
                    if board[rr][cc] == -1:
                        blocked = True
                        break
                if blocked:
                    continue
                cap = 1 if board[tr][tc] == -1 else 0
                moves.append((r, c, tr, tc, cap))
    return moves


def apply_move_and_flip(board, mv):
    """Apply move for current player (1), then flip perspective for next player."""
    fr, fc, tr, tc, _cap = mv
    nb = [row[:] for row in board]
    nb[fr][fc] = 0
    nb[tr][tc] = 1  # capture handled by overwrite
    # Flip to make next player be '1'
    for r in range(8):
        rr = nb[r]
        for c in range(8):
            rr[c] = -rr[c]
    return nb


def pieces_of(board, player):
    ps = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                ps.append((r, c))
    return ps


def group_stats(board, player):
    """Return (num_groups, largest_group_size, num_pieces). Connectivity is 8-directional."""
    ps = pieces_of(board, player)
    n = len(ps)
    if n == 0:
        return (0, 0, 0)
    seen = [[False] * 8 for _ in range(8)]
    groups = 0
    largest = 0
    for (sr, sc) in ps:
        if seen[sr][sc]:
            continue
        groups += 1
        q = deque()
        q.append((sr, sc))
        seen[sr][sc] = True
        size = 0
        while q:
            r, c = q.popleft()
            size += 1
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc) and not seen[rr][cc] and board[rr][cc] == player:
                    seen[rr][cc] = True
                    q.append((rr, cc))
        if size > largest:
            largest = size
    return (groups, largest, n)


def cohesion_score(board, player):
    """Compactness: smaller is better. Uses Chebyshev distance to centroid + bounding box area."""
    ps = pieces_of(board, player)
    if not ps:
        return 0.0
    rs = [p[0] for p in ps]
    cs = [p[1] for p in ps]
    cr = sum(rs) / len(ps)
    cc = sum(cs) / len(ps)
    cheb_sum = 0.0
    for r, c in ps:
        cheb_sum += max(abs(r - cr), abs(c - cc))
    rmin, rmax = min(rs), max(rs)
    cmin, cmax = min(cs), max(cs)
    area = (rmax - rmin + 1) * (cmax - cmin + 1)
    # Weight area more to encourage tight clusters
    return cheb_sum + 0.75 * area


def mobility(board, player):
    if player == 1:
        return len(generate_moves(board))
    # For opponent mobility, flip view cheaply by negation copy
    nb = [row[:] for row in board]
    for r in range(8):
        for c in range(8):
            nb[r][c] = -nb[r][c]
    return len(generate_moves(nb))


def eval_board(board):
    """
    Evaluation from side-to-move perspective (player == 1).
    Higher is better for current player.
    """
    my_g, my_largest, my_n = group_stats(board, 1)
    op_g, op_largest, op_n = group_stats(board, -1)

    # Terminal-ish conditions
    if my_n > 0 and my_g == 1:
        return 1_000_000
    if op_n > 0 and op_g == 1:
        return -1_000_000

    score = 0

    # Primary: connectivity (fewer groups is much better)
    score += (op_g - my_g) * 12000

    # Secondary: prefer having a large main component
    score += (my_largest - op_largest) * 150

    # Cohesion/compactness
    score += int((cohesion_score(board, -1) - cohesion_score(board, 1)) * 120)

    # Mobility (not too large, but helps avoid zugzwang-like bad positions)
    my_m = len(generate_moves(board))
    # Approx opponent mobility using negation
    nb = [row[:] for row in board]
    for r in range(8):
        for c in range(8):
            nb[r][c] = -nb[r][c]
    op_m = len(generate_moves(nb))
    score += (my_m - op_m) * 10

    # Slight center preference
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                score -= int((abs(r - CENTER) + abs(c - CENTER)) * 2)
            elif board[r][c] == -1:
                score += int((abs(r - CENTER) + abs(c - CENTER)) * 2)

    return score


def quick_move_heuristic(board, mv):
    """Fast move ordering heuristic without deep analysis."""
    fr, fc, tr, tc, cap = mv
    h = 0
    if cap:
        h += 80
    # Encourage landing adjacent to friendly pieces (helps connect)
    adj_friend = 0
    for dr, dc in DIRS:
        rr, cc = tr + dr, tc + dc
        if in_bounds(rr, cc) and board[rr][cc] == 1:
            adj_friend += 1
    h += adj_friend * 18

    # Mild center pull
    h -= int((abs(tr - CENTER) + abs(tc - CENTER)) * 2)

    # Discourage moving away from other pieces too much (crude)
    h -= int((abs(tr - fr) + abs(tc - fc)) * 1)

    return h


class Searcher:
    def __init__(self, time_limit=0.93):
        self.time_limit = time_limit
        self.t0 = None
        self.tt = {}  # (key, depth) -> value
        self.best_root = None

    def out_of_time(self):
        return (time.perf_counter() - self.t0) >= self.time_limit

    def negamax(self, board, depth, alpha, beta):
        if self.out_of_time():
            raise TimeoutError

        key = (board_to_key(board), depth)
        if key in self.tt:
            return self.tt[key]

        # Evaluate at leaf
        if depth == 0:
            v = eval_board(board)
            self.tt[key] = v
            return v

        moves = generate_moves(board)
        if not moves:
            # Should be extremely rare in LOA; treat as bad.
            v = -999_999
            self.tt[key] = v
            return v

        # Move ordering + beam-like pruning at deeper nodes
        moves.sort(key=lambda m: quick_move_heuristic(board, m), reverse=True)
        if depth >= 3 and len(moves) > 22:
            moves = moves[:22]
        elif depth == 2 and len(moves) > 28:
            moves = moves[:28]

        best = -10**18
        for mv in moves:
            nb = apply_move_and_flip(board, mv)
            val = -self.negamax(nb, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        self.tt[key] = best
        return best

    def search(self, board):
        # Always have a fallback legal move
        moves = generate_moves(board)
        if not moves:
            # No legal move: cannot guarantee legality; but this should not occur in arena states.
            return "0,0:0,0"

        # Immediate win check (no search)
        for mv in moves:
            # Apply move without flip to test current player's connectivity
            fr, fc, tr, tc, _ = mv
            nb = [row[:] for row in board]
            nb[fr][fc] = 0
            nb[tr][tc] = 1
            my_g, _, my_n = group_stats(nb, 1)
            if my_n > 0 and my_g == 1:
                return f"{fr},{fc}:{tr},{tc}"

        # Root ordering
        moves.sort(key=lambda m: quick_move_heuristic(board, m), reverse=True)
        self.best_root = moves[0]

        best_move = moves[0]
        best_val = -10**18

        # Iterative deepening
        depth = 1
        while True:
            if self.out_of_time():
                break
            try:
                cur_best_move = best_move
                cur_best_val = -10**18
                alpha, beta = -10**18, 10**18

                # At higher depths, consider only a prefix of root moves to control time.
                root_moves = moves
                if depth >= 4 and len(root_moves) > 18:
                    root_moves = root_moves[:18]
                elif depth == 3 and len(root_moves) > 26:
                    root_moves = root_moves[:26]

                for mv in root_moves:
                    if self.out_of_time():
                        raise TimeoutError
                    nb = apply_move_and_flip(board, mv)
                    val = -self.negamax(nb, depth - 1, -beta, -alpha)
                    if val > cur_best_val:
                        cur_best_val = val
                        cur_best_move = mv
                    if val > alpha:
                        alpha = val

                best_move, best_val = cur_best_move, cur_best_val
                depth += 1
            except TimeoutError:
                break

        fr, fc, tr, tc, _ = best_move
        return f"{fr},{fc}:{tr},{tc}"


def policy(board) -> str:
    """
    Arena API. board is 8x8 ints: 0 empty, 1 us, -1 opponent.
    Must return a legal move string: "from_row,from_col:to_row,to_col"
    """
    # Small safety: ensure board is plain list-of-lists
    b = [list(row) for row in board]

    s = Searcher(time_limit=0.93)
    s.t0 = time.perf_counter()
    move_str = s.search(b)

    # Final safety: if something went wrong, still return the first legal move.
    # (This should almost never trigger.)
    if move_str == "0,0:0,0":
        moves = generate_moves(b)
        if moves:
            fr, fc, tr, tc, _ = moves[0]
            return f"{fr},{fc}:{tr},{tc}"
    return move_str

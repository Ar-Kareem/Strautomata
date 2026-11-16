
import time

def policy(board):
    start_time = time.time()
    deadline = start_time + 0.95

    class TimeoutError(Exception):
        pass

    def check_time():
        if time.time() > deadline:
            raise TimeoutError

    WIN_SCORE = 1_000_000
    DIRS = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)]

    def idx(r, c):
        return r * 8 + c

    def coord(i):
        return (i // 8, i % 8)

    # Flatten the board
    flat = [board[r][c] for r in range(8) for c in range(8)]
    player = 1   # we are always 1

    # ---------- Helper functions ----------
    def count_line(board, r, c, dr, dc):
        """Total pieces on the whole line (row, column or diagonal)."""
        cnt = 0
        rr, cc = r, c
        while 0 <= rr < 8 and 0 <= cc < 8:
            if board[idx(rr, cc)] != 0:
                cnt += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            if board[idx(rr, cc)] != 0:
                cnt += 1
            rr -= dr
            cc -= dc
        return cnt

    def legal_moves(board, pl):
        """List of (from_index, to_index) legal moves for player pl."""
        moves = []
        for i in range(64):
            if board[i] == pl:
                r, c = coord(i)
                for dr, dc in DIRS:
                    N = count_line(board, r, c, dr, dc)
                    nr = r + dr * N
                    nc = c + dc * N
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        continue
                    to_i = idx(nr, nc)
                    if board[to_i] == pl:
                        continue      # cannot land on own piece
                    blocked = False
                    for step in range(1, N):
                        ir = r + dr * step
                        ic = c + dc * step
                        if board[idx(ir, ic)] == -pl:
                            blocked = True
                            break
                    if not blocked:
                        moves.append((i, to_i))
        return moves

    def make_move(board, move, pl):
        """Return a new board after applying the move."""
        fr, to = move
        new_board = board[:]          # shallow copy of flat list
        new_board[fr] = 0
        new_board[to] = pl
        return new_board

    def count_components(board, pl):
        """Number of 8‑connected components of player pl."""
        visited = set()
        comps = 0
        for i in range(64):
            if board[i] == pl and i not in visited:
                comps += 1
                stack = [i]
                visited.add(i)
                while stack:
                    cur = stack.pop()
                    r, c = coord(cur)
                    for dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            nidx = idx(nr, nc)
                            if board[nidx] == pl and nidx not in visited:
                                visited.add(nidx)
                                stack.append(nidx)
        return comps

    def sum_pairwise_chebyshev(piece_indices):
        """Sum of Chebyshev distances between all pairs of pieces."""
        coords = [coord(i) for i in piece_indices]
        total = 0
        n = len(coords)
        for i in range(n):
            r1, c1 = coords[i]
            for j in range(i + 1, n):
                r2, c2 = coords[j]
                total += max(abs(r1 - r2), abs(c1 - c2))
        return total

    def evaluate(board, root_pl):
        """Heuristic score from the perspective of root_pl."""
        my_pieces = [i for i in range(64) if board[i] == root_pl]
        opp_pieces = [i for i in range(64) if board[i] == -root_pl]

        my_count = len(my_pieces)
        opp_count = len(opp_pieces)

        my_comp = count_components(board, root_pl)
        opp_comp = count_components(board, -root_pl)

        # Terminal states (should have been caught earlier, but safe)
        if my_comp == 1:
            return WIN_SCORE
        if opp_comp == 1:
            return -WIN_SCORE

        piece_diff = my_count - opp_count
        comp_diff = opp_comp - my_comp                     # larger is good

        my_spread = sum_pairwise_chebyshev(my_pieces)
        opp_spread = sum_pairwise_chebyshev(opp_pieces)
        spread_diff = opp_spread - my_spread

        my_center = 0.0
        for i in my_pieces:
            r, c = coord(i)
            my_center += (r - 3.5) ** 2 + (c - 3.5) ** 2
        opp_center = 0.0
        for i in opp_pieces:
            r, c = coord(i)
            opp_center += (r - 3.5) ** 2 + (c - 3.5) ** 2
        center_diff = opp_center - my_center

        # Weights determined empirically
        score = (2000 * piece_diff +
                 1500 * comp_diff +
                 10 * spread_diff +
                 5 * center_diff)
        return int(score)

    def move_heuristic(board, move, pl):
        """Simple static move ordering: captures first, then centre improvement."""
        fr, to = move
        capture = board[to] == -pl
        base = 1000 if capture else 0
        r1, c1 = coord(fr)
        r2, c2 = coord(to)
        d1 = max(abs(r1 - 3.5), abs(c1 - 3.5))
        d2 = max(abs(r2 - 3.5), abs(c2 - 3.5))
        improvement = d1 - d2   # positive if moving toward centre
        return base + improvement

    # ---------- Search functions ----------
    def alpha_beta(board, depth, max_depth, alpha, beta, player_turn, root_player, deadline):
        check_time()
        moves = legal_moves(board, player_turn)

        if depth == 0:
            return evaluate(board, root_player)

        if not moves:   # player cannot move → loses
            ply = max_depth - depth
            if player_turn == root_player:
                return -WIN_SCORE + ply
            else:
                return WIN_SCORE - ply

        # Order moves
        moves.sort(key=lambda m: move_heuristic(board, m, player_turn), reverse=True)

        if player_turn == root_player:   # maximizing player
            value = -float('inf')
            for move in moves:
                new_board = make_move(board, move, player_turn)
                # Immediate win for the player who just moved
                if count_components(new_board, player_turn) == 1:
                    ply = max_depth - depth + 1
                    value = WIN_SCORE - ply
                    return value
                val = alpha_beta(new_board, depth - 1, max_depth, alpha, beta,
                                 -player_turn, root_player, deadline)
                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:   # minimizing player
            value = float('inf')
            for move in moves:
                new_board = make_move(board, move, player_turn)
                if count_components(new_board, player_turn) == 1:
                    ply = max_depth - depth + 1
                    value = -WIN_SCORE + ply
                    return value
                val = alpha_beta(new_board, depth - 1, max_depth, alpha, beta,
                                 -player_turn, root_player, deadline)
                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if value <= alpha:
                    break
            return value

    # ---------- Root logic ----------
    moves = legal_moves(flat, player)
    if not moves:   # should not happen, but fallback
        return "0,0:0,0"

    # Immediate winning move?
    for move in moves:
        new_board = make_move(flat, move, player)
        if count_components(new_board, player) == 1:
            fr, to = move
            r1, c1 = coord(fr); r2, c2 = coord(to)
            return f"{r1},{c1}:{r2},{c2}"

    # Initial ordering
    moves.sort(key=lambda m: move_heuristic(flat, m, player), reverse=True)
    best_move = moves[0]   # default

    # Iterative deepening
    depth = 1
    while depth <= 20:   # arbitrary upper bound
        try:
            check_time()
            move_vals = []
            for move in moves:
                check_time()
                new_board = make_move(flat, move, player)
                if count_components(new_board, player) == 1:
                    val = WIN_SCORE - 1   # immediate win, ply = 1
                else:
                    val = alpha_beta(new_board, depth - 1, depth,
                                     -float('inf'), float('inf'),
                                     -player, player, deadline)
                move_vals.append((move, val))
                if val > WIN_SCORE - 100:   # winning move found
                    fr, to = move
                    r1, c1 = coord(fr); r2, c2 = coord(to)
                    return f"{r1},{c1}:{r2},{c2}"

            # Sort by value for next depth
            move_vals.sort(key=lambda x: x[1], reverse=True)
            best_move, best_val = move_vals[0]
            moves = [m for m, v in move_vals]

            depth += 1
        except TimeoutError:
            break

    fr, to = best_move
    r1, c1 = coord(fr); r2, c2 = coord(to)
    return f"{r1},{c1}:{r2},{c2}"

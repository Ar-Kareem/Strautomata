
import time
import math

def policy(board) -> str:
    start_time = time.time()
    TIME_LIMIT = 0.85  # safety margin under 1.0 second

    # Convert board into flat or fast-indexed 8x8 list
    grid = [[0] * 8 for _ in range(8)]
    for r in range(8):
        for c in range(8):
            grid[r][c] = int(board[r][c])

    def get_lines_counts(b):
        row_c = [0] * 8
        col_c = [0] * 8
        d1_c = [0] * 15  # r - c + 7
        d2_c = [0] * 15  # r + c
        for r in range(8):
            for c in range(8):
                if b[r][c] != 0:
                    row_c[r] += 1
                    col_c[c] += 1
                    d1_c[r - c + 7] += 1
                    d2_c[r + c] += 1
        return row_c, col_c, d1_c, d2_c

    DIRECTIONS = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (1, 1), (-1, 1), (1, -1)
    ]

    def get_line_count(r, c, dr, dc, rc, cc, d1c, d2c):
        if dr == 0:
            return rc[r]
        elif dc == 0:
            return cc[c]
        elif dr == dc:
            return d1c[r - c + 7]
        else:
            return d2c[r + c]

    def get_pieces(b, player):
        pcs = []
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    pcs.append((r, c))
        return pcs

    def check_connected(pcs):
        if len(pcs) <= 1:
            return True
        pcs_set = set(pcs)
        start = pcs[0]
        q = [start]
        visited = {start}
        while q:
            r, c = q.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nbr = (r + dr, c + dc)
                    if nbr in pcs_set and nbr not in visited:
                        visited.add(nbr)
                        q.append(nbr)
        return len(visited) == len(pcs_set)

    def get_components_and_concentration(pcs):
        if not pcs:
            return 0, 0, 0
        n = len(pcs)
        if n == 1:
            return 1, 1, 0

        # Center of mass
        cr = sum(r for r, _ in pcs) / n
        cc = sum(c for _, c in pcs) / n
        dispersion = sum(max(abs(r - cr), abs(c - cc)) for r, c in pcs)

        # Components
        pcs_set = set(pcs)
        visited = set()
        components = 0
        max_comp_size = 0

        for p in pcs:
            if p not in visited:
                components += 1
                q = [p]
                visited.add(p)
                c_size = 0
                while q:
                    curr_r, curr_c = q.pop()
                    c_size += 1
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nbr = (curr_r + dr, curr_c + dc)
                            if nbr in pcs_set and nbr not in visited:
                                visited.add(nbr)
                                q.append(nbr)
                if c_size > max_comp_size:
                    max_comp_size = c_size

        return components, max_comp_size, dispersion

    def generate_legal_moves(b, player):
        moves = []
        rc, cc, d1c, d2c = get_lines_counts(b)
        opp = -player

        for r in range(8):
            for c in range(8):
                if b[r][c] != player:
                    continue

                for dr, dc in DIRECTIONS:
                    dist = get_line_count(r, c, dr, dc, rc, cc, d1c, d2c)
                    tr = r + dr * dist
                    tc = c + dc * dist

                    if not (0 <= tr < 8 and 0 <= tc < 8):
                        continue
                    if b[tr][tc] == player:
                        continue

                    # Path clearance check (cannot jump over opponent pieces)
                    blocked = False
                    for step in range(1, dist):
                        if b[r + dr * step][c + dc * step] == opp:
                            blocked = True
                            break
                    if not blocked:
                        is_capture = (b[tr][tc] == opp)
                        moves.append((r, c, tr, tc, is_capture))

        return moves

    def make_move(b, move, player):
        r, c, tr, tc, _ = move
        captured = b[tr][tc]
        b[tr][tc] = player
        b[r][c] = 0
        return captured

    def undo_move(b, move, player, captured):
        r, c, tr, tc, _ = move
        b[r][c] = player
        b[tr][tc] = captured

    def evaluate(b):
        p1_pieces = get_pieces(b, 1)
        p2_pieces = get_pieces(b, -1)

        p1_conn = check_connected(p1_pieces)
        p2_conn = check_connected(p2_pieces)

        if p1_conn and not p2_conn:
            return 100000.0
        if p2_conn and not p1_conn:
            return -100000.0
        if p1_conn and p2_conn:
            return 100000.0

        p1_comps, p1_max_c, p1_disp = get_components_and_concentration(p1_pieces)
        p2_comps, p2_max_c, p2_disp = get_components_and_concentration(p2_pieces)

        p1_ratio = p1_max_c / len(p1_pieces) if p1_pieces else 0
        p2_ratio = p2_max_c / len(p2_pieces) if p2_pieces else 0

        score = 0.0
        # Concentration is prime: lower dispersion is much better
        score += (p2_disp - p1_disp) * 15.0
        # Connected cluster ratio
        score += (p1_ratio - p2_ratio) * 120.0
        # Fewer components
        score += (p2_comps - p1_comps) * 40.0

        return score

    all_moves = generate_legal_moves(grid, 1)
    if not all_moves:
        return "0,0:0,0"

    # Immediate win search
    for m in all_moves:
        cap = make_move(grid, m, 1)
        pcs1 = get_pieces(grid, 1)
        if check_connected(pcs1):
            undo_move(grid, m, 1, cap)
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        undo_move(grid, m, 1, cap)

    best_move = all_moves[0]
    tt = {}

    def order_moves(moves, best_m=None):
        def move_weight(m):
            w = 0
            if best_m and m[:4] == best_m[:4]:
                w += 10000
            if m[4]:  # capture
                w += 100
            # Center target bias
            tr, tc = m[2], m[3]
            w += (3.5 - abs(tr - 3.5)) + (3.5 - abs(tc - 3.5))
            return w
        return sorted(moves, key=move_weight, reverse=True)

    def negamax(b, depth, alpha, beta, player):
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError()

        # Terminal checks
        p1_pieces = get_pieces(b, 1)
        p2_pieces = get_pieces(b, -1)
        p1_conn = check_connected(p1_pieces)
        p2_conn = check_connected(p2_pieces)

        if p1_conn or p2_conn:
            # Player who just moved to create simultaneous win wins
            # Previous mover was -player
            if -player == 1:
                return 100000.0 - (10 - depth)
            else:
                return -100000.0 + (10 - depth)

        if depth == 0:
            val = evaluate(b)
            return val if player == 1 else -val

        moves = generate_legal_moves(b, player)
        if not moves:
            # No moves: evaluate directly
            val = evaluate(b)
            return val if player == 1 else -val

        moves = order_moves(moves)
        max_eval = -float('inf')

        for m in moves:
            cap = make_move(b, m, player)
            # Immediate win check
            curr_pcs = get_pieces(b, player)
            if check_connected(curr_pcs):
                undo_move(b, m, player, cap)
                return 100000.0 - (10 - depth)

            try:
                ev = -negamax(b, depth - 1, -beta, -alpha, -player)
            finally:
                undo_move(b, m, player, cap)

            if ev > max_eval:
                max_eval = ev
            if max_eval > alpha:
                alpha = max_eval
            if alpha >= beta:
                break

        return max_eval

    # Iterative deepening
    ordered = order_moves(all_moves)
    for depth in range(1, 10):
        if time.time() - start_time > TIME_LIMIT:
            break
        current_best = None
        best_val = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        try:
            for m in ordered:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError()

                cap = make_move(grid, m, 1)
                curr_pcs = get_pieces(grid, 1)
                if check_connected(curr_pcs):
                    undo_move(grid, m, 1, cap)
                    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"

                val = -negamax(grid, depth - 1, -beta, -alpha, -1)
                undo_move(grid, m, 1, cap)

                if val > best_val:
                    best_val = val
                    current_best = m
                if val > alpha:
                    alpha = val

            if current_best is not None:
                best_move = current_best
                ordered = order_moves(all_moves, best_move)

        except TimeoutError:
            break

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

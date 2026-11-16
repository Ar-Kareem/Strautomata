
import collections

def policy(me, opponent, memory):
    N = 19
    ME = 1
    OPP = 2
    EMPTY = 0
    PASS = None
    DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

    # convert to 0‑based coordinates
    me0 = [(r-1,c-1) for r,c in me]
    opp0 = [(r-1,c-1) for r,c in opponent]

    # ------------------------------------------------------------
    # Helper functions
    # ------------------------------------------------------------
    def build_board(my_stones, op_stones):
        board = [[EMPTY]*N for _ in range(N)]
        for r,c in my_stones: board[r][c] = ME
        for r,c in op_stones: board[r][c] = OPP
        return board

    def encode(r,c): return r*N + c
    def decode(idx): return divmod(idx, N)

    def get_group(board, r, c, color):
        """Return (set of indices of the group, set of its liberty indices)."""
        if board[r][c] != color:
            return set(), set()
        visited = set()
        stack = [(r,c)]
        visited.add(encode(r,c))
        liberties = set()
        while stack:
            cr, cc = stack.pop()
            for dr,dc in DIRS:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < N and 0 <= nc < N:
                    if board[nr][nc] == EMPTY:
                        liberties.add(encode(nr,nc))
                    elif board[nr][nc] == color:
                        idx = encode(nr,nc)
                        if idx not in visited:
                            visited.add(idx)
                            stack.append((nr,nc))
        return visited, liberties

    def is_legal(board, color, move, ko_restrict):
        if move is PASS:
            return True
        r,c = move
        if board[r][c] != EMPTY:
            return False
        opp = 3 - color
        # temporarily place stone
        board[r][c] = color
        # find opponent groups that would be captured
        captured = set()
        visited_opp = set()
        for dr,dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == opp:
                idx = encode(nr,nc)
                if idx in visited_opp:
                    continue
                group, liberties = get_group(board, nr, nc, opp)
                visited_opp.update(group)
                if not liberties:
                    captured.update(group)
        # ko check: illegal if move is the ko point and captures exactly one stone
        if ko_restrict is not None and (r,c) == ko_restrict and len(captured) == 1:
            board[r][c] = EMPTY
            return False
        # check suicide after captures
        visited_my = set()
        stack = [(r,c)]
        visited_my.add(encode(r,c))
        my_liberties = set()
        while stack:
            cr, cc = stack.pop()
            for dr,dc in DIRS:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < N and 0 <= nc < N:
                    idx = encode(nr,nc)
                    if board[nr][nc] == EMPTY or idx in captured:
                        my_liberties.add(idx)
                    elif board[nr][nc] == color and idx not in visited_my:
                        visited_my.add(idx)
                        stack.append((nr,nc))
        board[r][c] = EMPTY
        return bool(my_liberties)

    def apply_move(board, color, move, ko_restrict):
        """Execute a legal move, modify board in place, return (new_ko, captured_set)."""
        r,c = move
        opp = 3 - color
        board[r][c] = color
        captured = set()
        visited_opp = set()
        for dr,dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == opp:
                idx = encode(nr,nc)
                if idx in visited_opp:
                    continue
                group, liberties = get_group(board, nr, nc, opp)
                visited_opp.update(group)
                if not liberties:
                    captured.update(group)
        for idx in captured:
            x,y = decode(idx)
            board[x][y] = EMPTY
        new_ko = None
        if len(captured) == 1:
            pt = next(iter(captured))
            new_ko = decode(pt)
        return new_ko, captured

    def bfs_distance_color(board, color):
        INF = 10**9
        dist = [[INF]*N for _ in range(N)]
        q = collections.deque()
        for r in range(N):
            for c in range(N):
                if board[r][c] == color:
                    dist[r][c] = 0
                    q.append((r,c))
        while q:
            r,c = q.popleft()
            d = dist[r][c]
            for dr,dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and dist[nr][nc] == INF:
                    dist[nr][nc] = d+1
                    q.append((nr,nc))
        return dist

    def bfs_distance_combined(board):
        INF = 10**9
        dist = [[INF]*N for _ in range(N)]
        q = collections.deque()
        for r in range(N):
            for c in range(N):
                if board[r][c] != EMPTY:
                    dist[r][c] = 0
                    q.append((r,c))
        while q:
            r,c = q.popleft()
            d = dist[r][c]
            for dr,dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and dist[nr][nc] == INF:
                    dist[nr][nc] = d+1
                    q.append((nr,nc))
        return dist

    def evaluate(board, pov_color):
        """Voronoi area difference from pov_color's perspective."""
        my_color = pov_color
        opp_color = 3 - my_color
        my_dist = bfs_distance_color(board, my_color)
        opp_dist = bfs_distance_color(board, opp_color)
        my_stones = opp_stones = 0
        my_terr = opp_terr = 0
        for r in range(N):
            for c in range(N):
                if board[r][c] == my_color:
                    my_stones += 1
                elif board[r][c] == opp_color:
                    opp_stones += 1
                else:
                    if my_dist[r][c] < opp_dist[r][c]:
                        my_terr += 1
                    elif opp_dist[r][c] < my_dist[r][c]:
                        opp_terr += 1
        return (my_stones + my_terr) - (opp_stones + opp_terr)

    # Predefined opening moves (0‑based coordinates)
    OPENING_MOVES = [
        (3,3),(3,15),(15,3),(15,15),           # 4‑4 points
        (2,2),(2,14),(14,2),(14,14),           # 3‑3 points
        (3,9),(9,3),(9,15),(15,9),             # side star points (4-10,10-4,…)
        (9,9),                                 # tengen
        (2,3),(3,2),(2,15),(3,14),             # 3‑4 points
        (14,3),(15,2),(14,15),(15,14)
    ]

    def get_candidates(board, color, ko_restrict, early=False):
        candidates = set()
        if early:
            for move in OPENING_MOVES:
                if is_legal(board, color, move, ko_restrict):
                    candidates.add(move)
        min_dist = bfs_distance_combined(board)
        thresh = 3 if early else 2
        for r in range(N):
            for c in range(N):
                if board[r][c] == EMPTY and min_dist[r][c] <= thresh:
                    if is_legal(board, color, (r,c), ko_restrict):
                        candidates.add((r,c))
        candidates.add(PASS)
        return list(candidates)

    # ------------------------------------------------------------
    # Current state
    # ------------------------------------------------------------
    board = build_board(me0, opp0)
    total_stones = len(me0) + len(opp0)
    early = total_stones < 20

    def stone_list_to_bit(stone_list):
        bit = 0
        for r,c in stone_list:
            bit |= (1 << encode(r,c))
        return bit

    me_cur_bit = stone_list_to_bit(me0)
    opp_cur_bit = stone_list_to_bit(opp0)

    if not memory:
        prev_me_bit = 0
        prev_opp_bit = 0
    else:
        prev_me_bit = memory.get('me_bit', 0)
        prev_opp_bit = memory.get('opp_bit', 0)

    added_opp = opp_cur_bit & ~prev_opp_bit
    removed_me = prev_me_bit & ~me_cur_bit

    ko_restrict = None
    if added_opp.bit_count() == 1 and removed_me.bit_count() == 1:
        idx = removed_me.bit_length() - 1   # only one bit set
        ko_restrict = decode(idx)

    # ------------------------------------------------------------
    # Generate and prune our candidate moves
    # ------------------------------------------------------------
    our_candidates_all = get_candidates(board, ME, ko_restrict, early=early)

    MAX_OUR = 25
    if len(our_candidates_all) > MAX_OUR:
        # quick ranking by static evaluation
        scores = []
        for move in our_candidates_all:
            if move is PASS:
                score = evaluate(board, ME)
            else:
                b_copy = [row[:] for row in board]
                apply_move(b_copy, ME, move, ko_restrict)
                score = evaluate(b_copy, ME)
            scores.append(score)
        ranked = sorted(zip(our_candidates_all, scores), key=lambda x: x[1], reverse=True)
        our_candidates = [m for m,_ in ranked[:MAX_OUR]]
    else:
        our_candidates = our_candidates_all

    best_move = None
    best_value = -float('inf')
    MAX_OPP = 20

    # ------------------------------------------------------------
    # Depth‑2 minimax
    # ------------------------------------------------------------
    for move in our_candidates:
        b1 = [row[:] for row in board]
        if move is PASS:
            ko1 = ko_restrict
        else:
            ko1, _ = apply_move(b1, ME, move, ko_restrict)
        stones_after = total_stones + (0 if move is PASS else 1)
        opp_early = stones_after < 20

        opp_candidates_all = get_candidates(b1, OPP, ko1, early=opp_early)

        if len(opp_candidates_all) > MAX_OPP:
            opp_scores = []
            for opp_move in opp_candidates_all:
                if opp_move is PASS:
                    score_opp = evaluate(b1, ME)
                else:
                    b2_copy = [row[:] for row in b1]
                    apply_move(b2_copy, OPP, opp_move, ko1)
                    score_opp = evaluate(b2_copy, ME)
                opp_scores.append(score_opp)
            opp_ranked = sorted(zip(opp_candidates_all, opp_scores), key=lambda x: x[1])
            opp_candidates = [om for om,_ in opp_ranked[:MAX_OPP]]
        else:
            opp_candidates = opp_candidates_all

        move_value = float('inf')
        abort = False
        for opp_move in opp_candidates:
            b2 = [row[:] for row in b1]
            if opp_move is not PASS:
                apply_move(b2, OPP, opp_move, ko1)
            score = evaluate(b2, ME)
            if score < move_value:
                move_value = score
            if move_value <= best_value:
                abort = True
                break
        if abort:
            continue
        if move_value > best_value:
            best_value = move_value
            best_move = move

    if best_move is None:
        best_move = our_candidates[0] if our_candidates else PASS

    # ------------------------------------------------------------
    # Prepare memory for next call
    # ------------------------------------------------------------
    if best_move is PASS:
        me_next_bit = me_cur_bit
        opp_next_bit = opp_cur_bit
    else:
        b_temp = [row[:] for row in board]
        _, captured_set = apply_move(b_temp, ME, best_move, ko_restrict)
        idx_move = encode(best_move[0], best_move[1])
        me_next_bit = me_cur_bit | (1 << idx_move)
        opp_next_bit = opp_cur_bit
        for idx in captured_set:
            opp_next_bit &= ~(1 << idx)

    memory_out = {'me_bit': me_next_bit, 'opp_bit': opp_next_bit}

    # ------------------------------------------------------------
    # Return action in 1‑based coordinates
    # ------------------------------------------------------------
    if best_move is PASS:
        action = (0,0)
    else:
        r,c = best_move
        action = (r+1, c+1)

    return action, memory_out


import copy
from collections import deque

# Lines of Action policy.
# Returns a move string "r0,c0:r1,c1".
def policy(board):
    PLAYER = 1
    OPP = -1

    DIRECTIONS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

    def in_bounds(r,c):
        return 0 <= r < 8 and 0 <= c < 8

    def count_in_line(b, r, c, dr, dc):
        # Count non-empty pieces on the whole line corresponding to direction (dr,dc)
        if dr == 0:
            # row
            cnt = 0
            for cc in range(8):
                if b[r][cc] != 0:
                    cnt += 1
            return cnt
        if dc == 0:
            # column
            cnt = 0
            for rr in range(8):
                if b[rr][c] != 0:
                    cnt += 1
            return cnt
        # diagonal
        if dr == dc:
            # main diagonal (r-c constant)
            const = r - c
            cnt = 0
            for rr in range(8):
                cc = rr - const
                if 0 <= cc < 8 and b[rr][cc] != 0:
                    cnt += 1
            return cnt
        else:
            # anti-diagonal (r+c constant)
            const = r + c
            cnt = 0
            for rr in range(8):
                cc = const - rr
                if 0 <= cc < 8 and b[rr][cc] != 0:
                    cnt += 1
            return cnt

    def generate_moves(b, player):
        moves = []
        for r in range(8):
            for c in range(8):
                if b[r][c] != player:
                    continue
                for (dr,dc) in DIRECTIONS:
                    dist = count_in_line(b, r, c, dr, dc)
                    tr = r + dr * dist
                    tc = c + dc * dist
                    if not in_bounds(tr, tc):
                        continue
                    # cannot land on friendly piece
                    if b[tr][tc] == player:
                        continue
                    # cannot jump over enemy pieces
                    blocked = False
                    for k in range(1, dist):
                        rr = r + dr*k
                        cc = c + dc*k
                        if b[rr][cc] == -player:
                            blocked = True
                            break
                    if blocked:
                        continue
                    # move is legal
                    moves.append((r,c,tr,tc))
        return moves

    def apply_move(b, move, player):
        r,c,tr,tc = move
        nb = [row[:] for row in b]
        nb[r][c] = 0
        nb[tr][tc] = player
        return nb

    def connected_components(b, player):
        visited = [[False]*8 for _ in range(8)]
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        comps = 0
        for r in range(8):
            for c in range(8):
                if b[r][c] == player and not visited[r][c]:
                    comps += 1
                    # BFS
                    dq = deque()
                    dq.append((r,c))
                    visited[r][c] = True
                    while dq:
                        rr,cc = dq.popleft()
                        for dr,dc in dirs:
                            nr, nc = rr+dr, cc+dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr][nc] and b[nr][nc] == player:
                                visited[nr][nc] = True
                                dq.append((nr,nc))
        return comps

    def centroid_distance_sum(b, player):
        pts = [(r,c) for r in range(8) for c in range(8) if b[r][c] == player]
        if not pts:
            return 1000
        sr = sum(p[0] for p in pts)
        sc = sum(p[1] for p in pts)
        cr = sr / len(pts)
        cc = sc / len(pts)
        ds = 0.0
        for (r,c) in pts:
            ds += abs(r - cr) + abs(c - cc)  # Manhattan to centroid
        return ds

    def evaluate(b):
        my_comps = connected_components(b, PLAYER)
        opp_comps = connected_components(b, OPP)
        if my_comps == 1:
            return 100000
        if opp_comps == 1:
            return -100000
        my_moves = len(generate_moves(b, PLAYER))
        opp_moves = len(generate_moves(b, OPP))
        compact = centroid_distance_sum(b, PLAYER)
        # Combine with weights: fewer components is strongly good; also prefer higher opponent components
        score = -2000 * my_comps + 800 * (opp_comps) - 10 * my_moves + 5 * opp_moves - int(compact)
        return score

    # Negamax with alpha-beta, depth in plies
    MAX_BRANCH = 60  # limit branching after ordering
    def negamax(b, depth, alpha, beta, player_to_move):
        if depth == 0:
            return evaluate(b)
        moves = generate_moves(b, player_to_move)
        if not moves:
            # No legal moves: evaluate statically
            return evaluate(b)
        # Move ordering: evaluate resulting boards quickly
        scored = []
        for mv in moves:
            nb = apply_move(b, mv, player_to_move)
            sc = evaluate(nb)
            scored.append((sc, mv))
        scored.sort(reverse=True, key=lambda x: x[0])
        # limit branching
        if len(scored) > MAX_BRANCH:
            scored = scored[:MAX_BRANCH]
        best = -10**9
        for sc, mv in scored:
            nb = apply_move(b, mv, player_to_move)
            val = -negamax(nb, depth-1, -beta, -alpha, -player_to_move)
            if val > best:
                best = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best

    # Root search: try moves and pick best
    root_moves = generate_moves(board, PLAYER)
    if not root_moves:
        # No legal move (very unlikely). Return a default invalid-sounding but legal fallback:
        # scan for any legal move again and return it
        for r in range(8):
            for c in range(8):
                if board[r][c] == PLAYER:
                    for dr,dc in DIRECTIONS:
                        dist = count_in_line(board, r, c, dr, dc)
                        tr = r + dr*dist
                        tc = c + dc*dist
                        if in_bounds(tr, tc) and board[tr][tc] != PLAYER:
                            blocked = False
                            for k in range(1, dist):
                                rr = r + dr*k
                                cc = c + dc*k
                                if board[rr][cc] == OPP:
                                    blocked = True
                                    break
                            if not blocked:
                                return f"{r},{c}:{tr},{tc}"
        # As ultimate fallback, return a no-op like moving first piece to itself is illegal,
        # but we must return a legal move - here we just raise (should not happen)
        raise RuntimeError("No legal moves available")
    # Order root moves by quick eval
    scored = []
    for mv in root_moves:
        nb = apply_move(board, mv, PLAYER)
        sc = evaluate(nb)
        scored.append((sc, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    if len(scored) > MAX_BRANCH:
        scored = scored[:MAX_BRANCH]

    best_val = -10**9
    best_move = scored[0][1]
    # search depth set to 2 plies (player -> opponent -> leaf)
    SEARCH_DEPTH = 2
    alpha = -10**9
    beta = 10**9
    for sc, mv in scored:
        nb = apply_move(board, mv, PLAYER)
        val = -negamax(nb, SEARCH_DEPTH-1, -beta, -alpha, OPP)
        if val > best_val:
            best_val = val
            best_move = mv
        alpha = max(alpha, val)
        if alpha >= beta:
            break

    r,c,tr,tc = best_move
    return f"{r},{c}:{tr},{tc}"

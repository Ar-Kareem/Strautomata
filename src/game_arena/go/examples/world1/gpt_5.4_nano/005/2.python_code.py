
import numpy as np
from collections import deque

BOARD_SIZE = 19

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    my = set(me)
    opp = set(opponent)
    N = BOARD_SIZE

    def inb(r, c):
        return 1 <= r <= N and 1 <= c <= N

    def neighbors(r, c):
        if r > 1: yield (r-1, c)
        if r < N: yield (r+1, c)
        if c > 1: yield (r, c-1)
        if c < N: yield (r, c+1)

    # Build board: 0 empty, 1 me, 2 opp
    board = np.zeros((N+1, N+1), dtype=np.int8)
    for r, c in my:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = 2

    # Compute group and liberties for a color at (r,c)
    def group_and_liberties(start_r, start_c):
        color = board[start_r, start_c]
        q = deque([(start_r, start_c)])
        seen = {(start_r, start_c)}
        libs = set()
        while q:
            r, c = q.popleft()
            for rr, cc in neighbors(r, c):
                if board[rr, cc] == 0:
                    libs.add((rr, cc))
                elif board[rr, cc] == color and (rr, cc) not in seen:
                    seen.add((rr, cc))
                    q.append((rr, cc))
        return seen, libs

    def would_capture_count(r, c):
        # For placing at empty (r,c), count captures of opponent groups with 0 libs after move.
        cap = 0
        for rr, cc in neighbors(r, c):
            if board[rr, cc] == 2:
                stones, libs = group_and_liberties(rr, cc)
                if len(libs) == 1 and (r, c) in libs:
                    cap += len(stones)
        return cap

    def is_suicide(r, c):
        # Place at empty (r,c); if our resulting group has no liberties and no capture, it's illegal.
        # With capture, it's legal even if "suicide-like".
        # Determine if move would capture any opponent stones:
        cap_any = would_capture_count(r, c) > 0

        # If no capture, check liberties of our prospective group after placement without captures.
        # We'll approximate by:
        # - If any adjacent empty -> not suicide
        # - Else if any adjacent friendly group has liberties>1 -> will remain with >0 libs
        # - Else if adjacent friendly groups all have exactly 1 liberty at (r,c) and no capture -> suicide
        adj_empty = any(board[rr, cc] == 0 for rr, cc in neighbors(r, c))
        if adj_empty:
            return False
        # no adjacent empties
        if cap_any:
            return False
        # Determine liberties for adjacent friendly groups
        # If any adjacent friendly group has a liberty besides (r,c), then not suicide.
        for rr, cc in neighbors(r, c):
            if board[rr, cc] == 1:
                stones, libs = group_and_liberties(rr, cc)
                if len(libs) > 1 or ((r, c) not in libs):
                    return False
        # otherwise suicide
        return True

    def legal_moves():
        # Return list of legal empty points (ignoring ko: not tracked in provided state)
        empties = np.argwhere(board[1:N+1, 1:N+1] == 0)
        moves = []
        for dr, dc in empties:
            r, c = int(dr) + 1 - 0, int(dc) + 1 - 0  # dr/dc are 0-based into slice
            # Actually: board indices are 1..N; empties computed on [1:N+1,1:N+1], so dr in 0..N-1
            r = int(dr) + 1
            c = int(dc) + 1
            if not is_suicide(r, c):
                moves.append((r, c))
        return moves

    # Identify groups in atari for both sides.
    # We'll compute atari lists by scanning stones (fast enough).
    def atari_groups(color):
        visited = set()
        res = []  # list of (stones_set, libs_set)
        for r in range(1, N+1):
            for c in range(1, N+1):
                if board[r, c] == color and (r, c) not in visited:
                    stones, libs = group_and_liberties(r, c)
                    visited |= stones
                    if len(libs) == 1:
                        res.append((stones, libs))
        return res

    my_atari = atari_groups(1)
    opp_atari = atari_groups(2)

    # 1) Captures: if we have a move that captures any opponent stones, play it (prefer max captures).
    legal = set(legal_moves())
    best = None
    best_cap = -1
    # Also collect capture moves in descending cap.
    for (r, c) in legal:
        cap = would_capture_count(r, c)
        if cap > best_cap:
            best_cap = cap
            best = (r, c)
    if best is not None and best_cap > 0:
        return best

    # 2) Defend in-atari stones: fill their unique liberty if legal.
    # If multiple, choose the move that simultaneously defends most.
    def_lib = {}
    for stones, libs in my_atari:
        (lr, lc) = next(iter(libs))
        def_lib[(lr, lc)] = def_lib.get((lr, lc), 0) + len(stones)

    candidate_def = [(move, score) for move, score in def_lib.items() if move in legal]
    if candidate_def:
        candidate_def.sort(key=lambda x: (-x[1], x[0]))
        return candidate_def[0][0]

    # 3) Otherwise, choose strategically:
    # - Prefer moves adjacent to opponent groups with low liberties (reduce their options).
    # - Prefer moves that create/expand our liberties (avoid giving them easy captures).
    center = (N + 1) / 2.0
    def heuristic_move(r, c):
        score = 0.0

        # Centrality
        dist = abs(r - center) + abs(c - center)
        score += (N - dist) * 0.3

        # Consider neighbors
        for rr, cc in neighbors(r, c):
            if board[rr, cc] == 2:
                stones, libs = group_and_liberties(rr, cc)
                # After we play here, that adjacent group loses one liberty if (r,c) is one of its libs.
                # Approximate "threat" as how close it is to atari.
                if (r, c) in libs:
                    if len(libs) == 2:
                        score += 6.0  # move puts them into atari
                    elif len(libs) == 3:
                        score += 2.5
                    elif len(libs) == 1:
                        score += 10.0
                # Also prefer taking away opponent liberties
                # More generally, favor attacking groups with small liberties.
                score += max(0, 5 - len(libs)) * 0.6
            elif board[rr, cc] == 1:
                stones, libs = group_and_liberties(rr, cc)
                # Encourage connecting and expanding our groups
                if (r, c) in libs:
                    score += 0.5
                score += max(0, len(libs) - 1) * 0.15

            # Adjacent empties: helps avoid suicide and builds mobility
            elif board[rr, cc] == 0:
                score += 0.25

        # Penalize moves that would allow immediate opponent capture next turn.
        # Approximate by: after our move, do opponent have a capturing move with cap>0?
        # We'll do limited check: if any adjacent opponent group would become capturable by a neighbor move.
        # Since time is tight, keep it light: simulate our move and compute if any adjacent empty-> opponent capture exists
        # by direct local scan around empties near (r,c).
        # Create a temp board for local evaluation.
        temp = board.copy()
        temp[r, c] = 1
        # Remove captured opponent stones
        for rr, cc in neighbors(r, c):
            if temp[rr, cc] == 2:
                stones, libs = group_and_liberties(rr, cc)
                if len(libs) == 1 and (r, c) in libs:
                    for sr, sc in stones:
                        temp[sr, sc] = 0
        # Now check if opponent can capture in one move around (r,c) neighborhood empties
        # We'll compute capture count for candidate neighbor empties only (local).
        local_checks = set()
        for rr, cc in neighbors(r, c):
            for r2, c2 in neighbors(rr, cc):
                if temp[r2, c2] == 0:
                    local_checks.add((r2, c2))
        # include (r,c) itself not empty
        def capture_count_on_temp(rr, cc):
            # count captures if opponent places at rr,cc
            cap = 0
            # temporarily place 2 at rr,cc
            # We'll check opponent's target groups: those that are adjacent and of color 1
            # But capture for opponent means capturing our stones (color 1 groups) with 0 libs.
            for a, b in neighbors(rr, cc):
                if temp[a, b] == 1:
                    # compute group libs in temp
                    color = temp[a, b]
                    q = deque([(a, b)])
                    seen = {(a, b)}
                    libs = set()
                    while q:
                        x, y = q.popleft()
                        for xx, yy in ( (x-1,y),(x+1,y),(x,y-1),(x,y+1) ):
                            if 1 <= xx <= N and 1 <= yy <= N:
                                if temp[xx, yy] == 0:
                                    libs.add((xx, yy))
                                elif temp[xx, yy] == color and (xx, yy) not in seen:
                                    seen.add((xx, yy))
                                    q.append((xx, yy))
                    if len(libs) == 1 and (rr, cc) in libs:
                        cap += len(seen)
            return cap

        # Penalize if opponent can capture >0 locally.
        opp_can_capture = False
        for x, y in local_checks:
            if capture_count_on_temp(x, y) > 0:
                opp_can_capture = True
                break
        if opp_can_capture:
            score -= 8.0

        return score

    best_move = None
    best_score = -1e18
    # 4) Candidate ordering: consider moves adjacent to existing stones first (usually stronger)
    neighbors_set = set()
    for r, c in my | opp:
        for rr, cc in neighbors(r, c):
            if board[rr, cc] == 0:
                neighbors_set.add((rr, cc))
    candidates = [m for m in neighbors_set if m in legal]
    if not candidates:
        candidates = list(legal)

    # If still huge, sample a bit by centrality
    candidates.sort(key=lambda m: abs(m[0]-center)+abs(m[1]-center))
    if len(candidates) > 80:
        candidates = candidates[:80]

    for r, c in candidates:
        s = heuristic_move(r, c)
        if s > best_score:
            best_score = s
            best_move = (r, c)

    if best_move is None:
        return (0, 0)
    return best_move

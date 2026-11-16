
import time
import math
from collections import deque

DIRS8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(board) -> str:
    start = time.time()
    TIME_LIMIT = 0.92

    def inb(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def clone(b):
        return [row[:] for row in b]

    def pieces_of(b, player):
        out = []
        for r in range(8):
            row = b[r]
            for c in range(8):
                if row[c] == player:
                    out.append((r, c))
        return out

    def line_count(b, r, c, dr, dc):
        cnt = 1
        rr, cc = r + dr, c + dc
        while inb(rr, cc):
            if b[rr][cc] != 0:
                cnt += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while inb(rr, cc):
            if b[rr][cc] != 0:
                cnt += 1
            rr -= dr
            cc -= dc
        return cnt

    def legal_moves(b, player):
        moves = []
        for r, c in pieces_of(b, player):
            for dr, dc in DIRS8:
                dist = line_count(b, r, c, dr, dc)
                tr, tc = r + dr * dist, c + dc * dist
                if not inb(tr, tc):
                    continue
                if b[tr][tc] == player:
                    continue

                ok = True
                rr, cc = r + dr, c + dc
                while (rr, cc) != (tr, tc):
                    if b[rr][cc] == -player:
                        ok = False
                        break
                    rr += dr
                    cc += dc
                if ok:
                    moves.append((r, c, tr, tc))
        return moves

    def apply_move(b, move, player):
        r, c, tr, tc = move
        nb = clone(b)
        nb[r][c] = 0
        nb[tr][tc] = player
        return nb

    def components_info(b, player):
        pcs = pieces_of(b, player)
        if not pcs:
            return 0, 0
        s = set(pcs)
        seen = set()
        comps = 0
        largest = 0
        for p in pcs:
            if p in seen:
                continue
            comps += 1
            q = [p]
            seen.add(p)
            size = 0
            while q:
                r, c = q.pop()
                size += 1
                for dr, dc in DIRS8:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in s and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        q.append((nr, nc))
            if size > largest:
                largest = size
        return comps, largest

    def is_connected(b, player):
        pcs = pieces_of(b, player)
        if len(pcs) <= 1:
            return True
        s = set(pcs)
        seen = set([pcs[0]])
        q = deque([pcs[0]])
        while q:
            r, c = q.popleft()
            for dr, dc in DIRS8:
                nr, nc = r + dr, c + dc
                if (nr, nc) in s and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return len(seen) == len(pcs)

    def winner(b):
        my_conn = is_connected(b, 1)
        opp_conn = is_connected(b, -1)
        if my_conn and opp_conn:
            return 1
        if my_conn:
            return 1
        if opp_conn:
            return -1
        return 0

    def centralization(b, player):
        score = 0.0
        for r, c in pieces_of(b, player):
            score += 7 - (abs(r - 3.5) + abs(c - 3.5))
        return score

    def bounding_box_area(b, player):
        pcs = pieces_of(b, player)
        if not pcs:
            return 64
        rs = [r for r, _ in pcs]
        cs = [c for _, c in pcs]
        return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)

    def evaluate(b):
        w = winner(b)
        if w == 1:
            return 10_000_000
        if w == -1:
            return -10_000_000

        my_comps, my_largest = components_info(b, 1)
        op_comps, op_largest = components_info(b, -1)
        my_n = len(pieces_of(b, 1))
        op_n = len(pieces_of(b, -1))

        my_mob = len(legal_moves(b, 1))
        op_mob = len(legal_moves(b, -1))

        score = 0
        score += 220 * (op_comps - my_comps)
        score += 35 * (my_largest - op_largest)
        score += 18 * (my_mob - op_mob)
        score += 8 * (centralization(b, 1) - centralization(b, -1))
        score += 10 * (bounding_box_area(b, -1) - bounding_box_area(b, 1))

        if my_n > 0:
            score += 140 * (my_largest / my_n)
        if op_n > 0:
            score -= 140 * (op_largest / op_n)

        return score

    def move_heuristic(b, move, player):
        r, c, tr, tc = move
        target = b[tr][tc]
        score = 0
        if target == -player:
            score += 500

        nb = apply_move(b, move, player)
        if is_connected(nb, player):
            score += 1_000_000
        if is_connected(nb, -player):
            score -= 900_000

        my_comps_before, my_largest_before = components_info(b, player)
        my_comps_after, my_largest_after = components_info(nb, player)
        op_comps_before, op_largest_before = components_info(b, -player)
        op_comps_after, op_largest_after = components_info(nb, -player)

        score += 180 * (my_comps_before - my_comps_after)
        score += 40 * (my_largest_after - my_largest_before)
        score += 120 * (op_comps_after - op_comps_before)
        score += 15 * ((7 - (abs(tr - 3.5) + abs(tc - 3.5))) - (7 - (abs(r - 3.5) + abs(c - 3.5))))
        return score

    def ordered_moves(b, player):
        moves = legal_moves(b, player)
        moves.sort(key=lambda m: move_heuristic(b, m, player), reverse=True)
        return moves

    all_moves = legal_moves(board, 1)
    if not all_moves:
        return "0,0:0,0"

    # Immediate win
    for mv in all_moves:
        nb = apply_move(board, mv, 1)
        if is_connected(nb, 1):
            return f"{mv[0]},{mv[1]}:{mv[2]},{mv[3]}"

    best_move = sorted(all_moves, key=lambda m: move_heuristic(board, m, 1), reverse=True)[0]

    def alphabeta(b, depth, alpha, beta, player):
        if time.time() - start > TIME_LIMIT:
            raise TimeoutError

        w = winner(b)
        if depth == 0 or w != 0:
            return evaluate(b)

        moves = ordered_moves(b, player)
        if not moves:
            return evaluate(b)

        if player == 1:
            val = -math.inf
            for mv in moves:
                nb = apply_move(b, mv, player)
                val = max(val, alphabeta(nb, depth - 1, alpha, beta, -player))
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            val = math.inf
            for mv in moves:
                nb = apply_move(b, mv, player)
                val = min(val, alphabeta(nb, depth - 1, alpha, beta, -player))
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val

    try:
        depth = 1
        while True:
            if time.time() - start > TIME_LIMIT:
                break
            moves = ordered_moves(board, 1)
            current_best = best_move
            current_best_val = -math.inf
            alpha = -math.inf
            beta = math.inf
            for mv in moves:
                if time.time() - start > TIME_LIMIT:
                    raise TimeoutError
                nb = apply_move(board, mv, 1)
                val = alphabeta(nb, depth - 1, alpha, beta, -1)
                if val > current_best_val:
                    current_best_val = val
                    current_best = mv
                alpha = max(alpha, current_best_val)
            best_move = current_best
            depth += 1
    except TimeoutError:
        pass
    except Exception:
        pass

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

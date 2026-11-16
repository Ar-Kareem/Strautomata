
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # ---------- Helpers ----------
    N = 8
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    EMPTY = 0

    def inb(r, c):
        return 0 <= r < N and 0 <= c < N

    def gen_legal_and_flips(you_b, opp_b):
        # returns list of (r,c, flips_mask as list of (r,c))
        empties = np.argwhere((you_b == 0) & (opp_b == 0))
        legal = []
        for r, c in empties:
            total_flips = []
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                line = []
                while inb(rr, cc) and opp_b[rr, cc] == 1:
                    line.append((rr, cc))
                    rr += dr
                    cc += dc
                if line and inb(rr, cc) and you_b[rr, cc] == 1:
                    total_flips.extend(line)
            if total_flips:
                legal.append((r, c, total_flips))
        return legal

    def apply_move(you_b, opp_b, move_rc, flips):
        r, c = move_rc
        new_you = you_b.copy()
        new_opp = opp_b.copy()
        new_you[r, c] = 1
        for fr, fc in flips:
            new_you[fr, fc] = 1
            new_opp[fr, fc] = 0
        return new_you, new_opp

    def count_discs(b):
        return int(b.sum())

    # Corner & near-corner strategy
    corners = [(0,0),(0,7),(7,0),(7,7)]
    # squares adjacent to corners (the "poisoned" ones depend on corner occupancy)
    adj = {
        (0,0): [(0,1),(1,0),(1,1)],
        (0,7): [(0,6),(1,7),(1,6)],
        (7,0): [(6,0),(7,1),(6,1)],
        (7,7): [(6,7),(7,6),(6,6)]
    }

    def heuristic(you_b, opp_b):
        # Feature-based evaluation from the perspective of "you"
        my = count_discs(you_b)
        op = count_discs(opp_b)
        empty = N*N - my - op

        # Corner scoring (very strong)
        corner_score = 0
        for cr, cc in corners:
            if you_b[cr, cc] == 1:
                corner_score += 25
            elif opp_b[cr, cc] == 1:
                corner_score -= 25

        # Avoid giving opponent access by penalizing adjacent squares when corner is empty
        poison_score = 0
        for corner, squares in adj.items():
            cr, cc = corner
            if you_b[cr, cc] == 0 and opp_b[cr, cc] == 0:
                # corner empty: playing in adjacent squares can be bad
                for sr, sc in squares:
                    if you_b[sr, sc] == 1:
                        poison_score -= 10
                    elif opp_b[sr, sc] == 1:
                        poison_score += 10

        # Mobility (legal move count)
        my_legals = gen_legal_and_flips(you_b, opp_b)
        op_legals = gen_legal_and_flips(opp_b, you_b)
        my_mob = len(my_legals)
        op_mob = len(op_legals)
        mobility_score = 0
        if my_mob + op_mob > 0:
            mobility_score = 3.0 * (my_mob - op_mob)

        # Disc difference (small influence early; more influence later)
        disc_diff = my - op
        phase = 1.0 - (empty / (N*N))  # 0 early, 1 late
        disc_score = (1.5 * phase + 0.3) * disc_diff

        # Parity / tempo: prefer moves that reduce opponent mobility a bit via empty squares
        # (lightweight)
        tempo_score = 0.1 * (empty if empty > 0 else 0)

        return corner_score + poison_score + mobility_score + disc_score + tempo_score

    # ---------- Minimax (alpha-beta), shallow for speed ----------
    def best_move(you_b, opp_b, depth):
        legal = gen_legal_and_flips(you_b, opp_b)
        if not legal:
            return None

        # Move ordering: corners and better immediate flips first
        def move_key(item):
            r, c, flips = item
            score = 0
            if (r, c) in corners:
                score += 1000
            # immediate flips
            score += len(flips) * 5
            # near-corner penalty if corner empty
            for corner, squares in adj.items():
                cr, cc = corner
                if you_b[cr, cc] == 0 and opp_b[cr, cc] == 0 and (r, c) in squares:
                    score -= 80
            return -score  # ascending for best first after using sort with key

        legal_sorted = sorted(legal, key=move_key)

        alpha = -10**9
        beta = 10**9
        best = legal_sorted[0]
        best_val = -10**9

        for r, c, flips in legal_sorted:
            n_you, n_opp = apply_move(you_b, opp_b, (r, c), flips)
            val = minimax(n_you, n_opp, depth - 1, alpha, beta)
            if val > best_val:
                best_val = val
                best = (r, c)
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break
        return best

    def minimax(you_b, opp_b, depth, alpha, beta):
        legal = gen_legal_and_flips(you_b, opp_b)
        if depth == 0 or not legal:
            # If no legal moves, game might still continue with opponent
            # Handle pass by switching roles
            if not legal:
                opp_legal = gen_legal_and_flips(opp_b, you_b)
                if not opp_legal:
                    # terminal: no one can move -> return final heuristic
                    return heuristic(you_b, opp_b)
                # pass turn
                return -minimax(opp_b, you_b, depth - 1, -beta, -alpha)
            return heuristic(you_b, opp_b)

        # Max node: "you_b" is current player; return value for that player.
        # We'll use negamax: value for current player; opponent is symmetric.
        value_best = -10**9
        legal_sorted = legal

        # Order: prefer corners first for pruning
        def order_key(item):
            r, c, flips = item
            score = 0
            if (r, c) in corners:
                score += 1000
            score += len(flips) * 5
            return -score
        legal_sorted = sorted(legal_sorted, key=order_key)

        for r, c, flips in legal_sorted:
            n_you, n_opp = apply_move(you_b, opp_b, (r, c), flips)
            val = -minimax(n_opp, n_you, depth - 1, -beta, -alpha)
            value_best = max(value_best, val)
            alpha = max(alpha, value_best)
            if alpha >= beta:
                break
        return value_best

    # ---------- Main ----------
    you_b = you.astype(np.int8)
    opp_b = opponent.astype(np.int8)

    # Depth adaptation by phase: more depth later when fewer moves
    my = int(you_b.sum())
    op = int(opp_b.sum())
    empty = 64 - my - op
    # Keep within speed: depth 3 early/mid, depth 4 if very low branching
    depth = 3
    if empty <= 16:
        depth = 4
    elif empty <= 28:
        depth = 3
    else:
        depth = 3

    move_rc = best_move(you_b, opp_b, depth=depth)
    if move_rc is None:
        return "pass"

    r, c = move_rc
    return chr(ord('a') + c) + str(r + 1)


import time
import numpy as np

FULL = (1 << 64) - 1
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Standard strong Othello positional weights
W = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

CORNERS = [0, 7, 56, 63]
CORNER_NEIGHBORS = {
    0:  [1, 8, 9],
    7:  [6, 14, 15],
    56: [48, 49, 57],
    63: [54, 55, 62],
}

INF = 10**9

def idx_to_move(idx: int) -> str:
    return chr(ord('a') + (idx & 7)) + str((idx >> 3) + 1)

def popcount(x: int) -> int:
    return x.bit_count()

def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    p = 0
    o = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if int(you[r][c]) == 1:
                p |= bit
            elif int(opponent[r][c]) == 1:
                o |= bit
    return p, o

def flips_for_move(idx: int, player: int, opp: int) -> int:
    bit = 1 << idx
    if (player | opp) & bit:
        return 0

    r = idx >> 3
    c = idx & 7
    flips = 0

    for dr, dc in DIRS:
        rr = r + dr
        cc = c + dc
        line = 0
        seen_opp = False

        while 0 <= rr < 8 and 0 <= cc < 8:
            b = 1 << (rr * 8 + cc)
            if opp & b:
                seen_opp = True
                line |= b
            elif player & b:
                if seen_opp:
                    flips |= line
                break
            else:
                break
            rr += dr
            cc += dc

    return flips

def legal_moves(player: int, opp: int):
    occ = player | opp
    moves = []
    empties = (~occ) & FULL
    while empties:
        lsb = empties & -empties
        idx = lsb.bit_length() - 1
        f = flips_for_move(idx, player, opp)
        if f:
            moves.append((idx, f))
        empties ^= lsb
    return moves

def apply_move(player: int, opp: int, idx: int, flips: int):
    bit = 1 << idx
    new_player = player | bit | flips
    new_opp = opp & ~flips
    return new_player, new_opp

def weighted_disc_score(player: int, opp: int) -> int:
    s = 0
    x = player
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        s += W[idx]
        x ^= lsb
    x = opp
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        s -= W[idx]
        x ^= lsb
    return s

def corner_score(player: int, opp: int) -> int:
    s = 0
    for c in CORNERS:
        b = 1 << c
        if player & b:
            s += 1
        elif opp & b:
            s -= 1
    return s

def corner_danger_score(player: int, opp: int) -> int:
    s = 0
    occ = player | opp
    for corner in CORNERS:
        cb = 1 << corner
        if occ & cb:
            continue
        for n in CORNER_NEIGHBORS[corner]:
            nb = 1 << n
            if player & nb:
                s -= 1
            elif opp & nb:
                s += 1
    return s

def frontier_score(player: int, opp: int) -> int:
    # Discs adjacent to at least one empty square are frontier discs.
    # Fewer frontier discs is usually better.
    occ = player | opp
    empty = (~occ) & FULL
    if empty == 0:
        return 0

    pf = 0
    of = 0
    x = empty
    seen = 0
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        r = idx >> 3
        c = idx & 7
        for dr, dc in DIRS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                b = 1 << (rr * 8 + cc)
                if not (seen & b):
                    if player & b:
                        pf += 1
                        seen |= b
                    elif opp & b:
                        of += 1
                        seen |= b
        x ^= lsb
    return of - pf

def evaluate(player: int, opp: int, passed: bool) -> int:
    occ = player | opp
    empties = 64 - popcount(occ)

    my_moves = legal_moves(player, opp)
    opp_moves = legal_moves(opp, player)

    if not my_moves and not opp_moves:
        diff = popcount(player) - popcount(opp)
        if diff > 0:
            return 1000000 + diff
        if diff < 0:
            return -1000000 + diff
        return 0

    mobility = len(my_moves) - len(opp_moves)
    corners = corner_score(player, opp)
    danger = corner_danger_score(player, opp)
    pos = weighted_disc_score(player, opp)
    frontier = frontier_score(player, opp)
    disc_diff = popcount(player) - popcount(opp)

    # Phase-dependent weighting
    if empties > 40:
        return (
            90 * corners +
            18 * mobility +
            12 * danger +
            8 * frontier +
            2 * pos
        )
    elif empties > 16:
        return (
            120 * corners +
            20 * mobility +
            10 * danger +
            8 * frontier +
            4 * pos +
            2 * disc_diff
        )
    else:
        return (
            160 * corners +
            16 * mobility +
            8 * danger +
            4 * frontier +
            3 * pos +
            20 * disc_diff
        )

def order_moves(moves, player: int, opp: int, tt_move=None):
    scored = []
    for idx, flips in moves:
        score = 0
        if idx in CORNERS:
            score += 100000
        score += 200 * W[idx]
        score += 8 * popcount(flips)

        # Prefer moves that reduce opponent mobility a bit, but cheaply.
        np, no = apply_move(player, opp, idx, flips)
        opp_mob = len(legal_moves(no, np))
        score -= 25 * opp_mob

        if tt_move is not None and idx == tt_move:
            score += 500000
        scored.append((score, idx, flips))
    scored.sort(reverse=True)
    return [(idx, flips) for score, idx, flips in scored]

class SearchTimeout(Exception):
    pass

class Engine:
    def __init__(self, deadline: float):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.perf_counter() >= self.deadline:
            raise SearchTimeout

    def negamax(self, player: int, opp: int, depth: int, alpha: int, beta: int, passed: bool):
        self.check_time()

        key = (player, opp, depth, passed)
        if key in self.tt:
            entry = self.tt[key]
            return entry[0], entry[1]

        moves = legal_moves(player, opp)

        if depth == 0:
            val = evaluate(player, opp, passed)
            self.tt[key] = (val, None)
            return val, None

        if not moves:
            opp_moves = legal_moves(opp, player)
            if not opp_moves:
                val = evaluate(player, opp, True)
                self.tt[key] = (val, None)
                return val, None
            val, _ = self.negamax(opp, player, depth, -beta, -alpha, True)
            val = -val
            self.tt[key] = (val, None)
            return val, None

        tt_move = self.tt.get((player, opp, depth - 1, False), (None, None))[1]
        moves = order_moves(moves, player, opp, tt_move)

        best_val = -INF
        best_move = moves[0][0]

        for idx, flips in moves:
            np, no = apply_move(player, opp, idx, flips)
            val, _ = self.negamax(no, np, depth - 1, -beta, -alpha, False)
            val = -val

            if val > best_val:
                best_val = val
                best_move = idx

            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                break

        self.tt[key] = (best_val, best_move)
        return best_val, best_move

def choose_depth(empties: int) -> int:
    if empties <= 10:
        return empties + 2
    if empties <= 14:
        return 10
    if empties <= 20:
        return 8
    if empties <= 32:
        return 6
    return 5

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    player, opp = arrays_to_bitboards(you, opponent)
    moves = legal_moves(player, opp)

    if not moves:
        return "pass"

    # Guaranteed legal fallback
    fallback_idx = order_moves(moves, player, opp)[0][0]
    best_idx = fallback_idx

    occ = player | opp
    empties = 64 - popcount(occ)

    # Conservative time budget
    deadline = time.perf_counter() + 0.92
    engine = Engine(deadline)

    max_depth = choose_depth(empties)

    try:
        # Iterative deepening
        start_depth = 1 if empties <= 12 else 2
        for depth in range(start_depth, max_depth + 1):
            val, idx = engine.negamax(player, opp, depth, -INF, INF, False)
            if idx is not None:
                best_idx = idx
            if time.perf_counter() >= deadline:
                break
    except SearchTimeout:
        pass
    except Exception:
        # Safety: always return a legal move.
        best_idx = fallback_idx

    # Final legality check in case of unexpected issues
    legal_idx_set = {idx for idx, _ in moves}
    if best_idx not in legal_idx_set:
        best_idx = fallback_idx

    return idx_to_move(best_idx)

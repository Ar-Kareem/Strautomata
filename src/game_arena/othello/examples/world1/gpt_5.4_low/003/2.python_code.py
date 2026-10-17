
import time
import numpy as np

# 8 directions
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Classic Othello positional weights
WEIGHTS = [
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120],
]

CORNERS = [0, 7, 56, 63]
X_SQUARES = [9, 14, 49, 54]
C_SQUARES = [1, 8, 6, 15, 48, 57, 55, 62]

# Adjacent-to-corner groups for corner-closeness penalty
CORNER_ADJ = {
    0:  [1, 8, 9],
    7:  [6, 14, 15],
    56: [48, 49, 57],
    63: [54, 55, 62],
}

ALL_MASK = (1 << 64) - 1


def rc_to_idx(r, c):
    return r * 8 + c


def idx_to_move(idx):
    return chr(ord('a') + (idx % 8)) + str((idx // 8) + 1)


def popcount(x):
    return x.bit_count()


def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    me = 0
    opp = 0
    # row-major, bit idx = r*8+c
    for r in range(8):
        for c in range(8):
            if int(you[r][c]) == 1:
                me |= 1 << (r * 8 + c)
            elif int(opponent[r][c]) == 1:
                opp |= 1 << (r * 8 + c)
    return me, opp


def bit_at(bb, idx):
    return (bb >> idx) & 1


def empty_at(me, opp, idx):
    return ((me | opp) >> idx) & 1 == 0


def legal_moves(me, opp):
    occupied = me | opp
    moves = []
    for idx in range(64):
        if (occupied >> idx) & 1:
            continue
        r, c = divmod(idx, 8)
        if is_legal_move(me, opp, r, c):
            moves.append(idx)
    return moves


def is_legal_move(me, opp, r, c):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        seen_opp = False
        while 0 <= rr < 8 and 0 <= cc < 8:
            idx = rr * 8 + cc
            if bit_at(opp, idx):
                seen_opp = True
            elif bit_at(me, idx):
                if seen_opp:
                    return True
                break
            else:
                break
            rr += dr
            cc += dc
    return False


def apply_move(me, opp, idx):
    r, c = divmod(idx, 8)
    flips = 0

    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = 0
        seen_opp = False
        while 0 <= rr < 8 and 0 <= cc < 8:
            j = rr * 8 + cc
            bit = 1 << j
            if opp & bit:
                seen_opp = True
                line |= bit
            elif me & bit:
                if seen_opp:
                    flips |= line
                break
            else:
                break
            rr += dr
            cc += dc

    move_bit = 1 << idx
    new_me = me | move_bit | flips
    new_opp = opp & (~flips & ALL_MASK)
    return new_opp, new_me  # swapped for negamax convenience


def game_over(me, opp):
    if (me | opp) == ALL_MASK:
        return True
    return len(legal_moves(me, opp)) == 0 and len(legal_moves(opp, me)) == 0


def frontier_count(me, opp):
    empty = ~(me | opp) & ALL_MASK
    count = 0
    bb = me
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        r, c = divmod(idx, 8)
        frontier = False
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                j = rr * 8 + cc
                if (empty >> j) & 1:
                    frontier = True
                    break
        if frontier:
            count += 1
        bb ^= lsb
    return count


def positional_score(me, opp):
    s = 0
    bb = me
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        r, c = divmod(idx, 8)
        s += WEIGHTS[r][c]
        bb ^= lsb
    bb = opp
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        r, c = divmod(idx, 8)
        s -= WEIGHTS[r][c]
        bb ^= lsb
    return s


def corner_score(me, opp):
    my_corners = sum((me >> i) & 1 for i in CORNERS)
    opp_corners = sum((opp >> i) & 1 for i in CORNERS)
    return 50 * (my_corners - opp_corners)


def corner_closeness(me, opp):
    score = 0
    for corner, adjs in CORNER_ADJ.items():
        if not bit_at(me | opp, corner):
            my_adj = sum((me >> a) & 1 for a in adjs)
            opp_adj = sum((opp >> a) & 1 for a in adjs)
            score += 12 * (opp_adj - my_adj)
    return score


def evaluate(me, opp):
    my_moves = legal_moves(me, opp)
    opp_moves = legal_moves(opp, me)

    if not my_moves and not opp_moves:
        diff = popcount(me) - popcount(opp)
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    empties = 64 - popcount(me | opp)

    pos = positional_score(me, opp)
    corners = corner_score(me, opp)
    close = corner_closeness(me, opp)

    mobility = 0
    if my_moves or opp_moves:
        mobility = 100 * (len(my_moves) - len(opp_moves)) / (len(my_moves) + len(opp_moves) + 1)

    my_front = frontier_count(me, opp)
    opp_front = frontier_count(opp, me)
    frontier = -20 * (my_front - opp_front) / (my_front + opp_front + 1)

    disc_diff = 0
    if empties <= 14:
        disc_diff = 8 * (popcount(me) - popcount(opp))

    # Early/midgame emphasizes mobility and corners; endgame adds disc difference.
    if empties > 40:
        return int(1.2 * pos + 3.5 * corners + 2.5 * close + 2.8 * mobility + 1.5 * frontier)
    elif empties > 16:
        return int(1.5 * pos + 4.0 * corners + 2.0 * close + 2.5 * mobility + 1.4 * frontier + 0.3 * disc_diff)
    else:
        return int(1.2 * pos + 4.5 * corners + 1.5 * close + 1.8 * mobility + 1.0 * frontier + 1.5 * disc_diff)


def move_order_key(idx, me, opp):
    # Higher is better.
    if idx in CORNERS:
        return 100000
    r, c = divmod(idx, 8)
    score = WEIGHTS[r][c]

    # Penalize adjacency to empty corners
    for corner, adjs in CORNER_ADJ.items():
        if idx in adjs and not bit_at(me | opp, corner):
            score -= 60

    # Small estimate based on immediate flips
    flips = 0
    rr0, cc0 = r, c
    for dr, dc in DIRS:
        rr, cc = rr0 + dr, cc0 + dc
        line = 0
        seen_opp = False
        while 0 <= rr < 8 and 0 <= cc < 8:
            j = rr * 8 + cc
            if bit_at(opp, j):
                seen_opp = True
                line += 1
            elif bit_at(me, j):
                if seen_opp:
                    flips += line
                break
            else:
                break
            rr += dr
            cc += dc
    score += flips
    return score


class Searcher:
    def __init__(self, time_limit):
        self.start = time.perf_counter()
        self.time_limit = time_limit
        self.tt = {}
        self.timeout = False

    def time_up(self):
        return (time.perf_counter() - self.start) >= self.time_limit

    def negamax(self, me, opp, depth, alpha, beta, passed=False):
        if self.time_up():
            self.timeout = True
            return 0

        key = (me, opp, depth, passed)
        if key in self.tt:
            return self.tt[key]

        moves = legal_moves(me, opp)

        if depth == 0:
            val = evaluate(me, opp)
            self.tt[key] = val
            return val

        if not moves:
            if passed:
                val = evaluate(me, opp)
                self.tt[key] = val
                return val
            val = -self.negamax(opp, me, depth, -beta, -alpha, True)
            if not self.timeout:
                self.tt[key] = val
            return val

        best = -10**9
        moves.sort(key=lambda m: move_order_key(m, me, opp), reverse=True)

        for mv in moves:
            nme, nopp = apply_move(me, opp, mv)
            val = -self.negamax(nme, nopp, depth - 1, -beta, -alpha, False)
            if self.timeout:
                return 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        self.tt[key] = best
        return best

    def choose(self, me, opp):
        moves = legal_moves(me, opp)
        if not moves:
            return "pass"

        # Safe fallback
        moves.sort(key=lambda m: move_order_key(m, me, opp), reverse=True)
        best_move = moves[0]

        empties = 64 - popcount(me | opp)
        if empties <= 10:
            max_depth = empties + 2
            time_limit = min(self.time_limit, 0.95)
        elif empties <= 14:
            max_depth = 10
            time_limit = min(self.time_limit, 0.9)
        elif empties <= 20:
            max_depth = 7
            time_limit = min(self.time_limit, 0.8)
        elif empties <= 40:
            max_depth = 6
            time_limit = min(self.time_limit, 0.7)
        else:
            max_depth = 5
            time_limit = min(self.time_limit, 0.55)

        self.time_limit = time_limit

        # Iterative deepening
        for depth in range(1, max_depth + 1):
            if self.time_up():
                break

            current_best = best_move
            current_best_val = -10**9

            ordered = sorted(moves, key=lambda m: move_order_key(m, me, opp), reverse=True)

            for mv in ordered:
                if self.time_up():
                    self.timeout = True
                    break
                nme, nopp = apply_move(me, opp, mv)
                val = -self.negamax(nme, nopp, depth - 1, -10**9, 10**9, False)
                if self.timeout:
                    break
                if val > current_best_val:
                    current_best_val = val
                    current_best = mv

            if not self.timeout:
                best_move = current_best
            else:
                break

        return idx_to_move(best_move)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    me, opp = arrays_to_bitboards(you, opponent)
    moves = legal_moves(me, opp)
    if not moves:
        return "pass"

    # Slight buffer under 1 second arena limit
    searcher = Searcher(time_limit=0.92)
    move = searcher.choose(me, opp)

    # Absolute legality safeguard
    legal_strs = {idx_to_move(m) for m in moves}
    if move in legal_strs:
        return move

    # Fallback should never fail
    return idx_to_move(moves[0])

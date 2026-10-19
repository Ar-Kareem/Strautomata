
import numpy as np
import time

# Directions: (dr, dc)
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

FILES = "abcdefgh"

# Positional weights (classic Othello-inspired table)
PST = np.array([
    [120, -20,  20,  5,  5, 20, -20, 120],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [120, -20,  20,  5,  5, 20, -20, 120],
], dtype=np.int32)

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
X_SQUARES = {
    (1, 1): (0, 0),
    (1, 6): (0, 7),
    (6, 1): (7, 0),
    (6, 6): (7, 7),
}
C_SQUARES = {
    (0, 1): (0, 0), (1, 0): (0, 0),
    (0, 6): (0, 7), (1, 7): (0, 7),
    (6, 0): (7, 0), (7, 1): (7, 0),
    (6, 7): (7, 7), (7, 6): (7, 7),
}

INF = 10**9


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def move_to_str(move):
    if move is None:
        return "pass"
    r, c = move
    return FILES[c] + str(r + 1)


def legal_moves(you, opp):
    empties = (you | opp) == 0
    moves = []
    for r in range(8):
        for c in range(8):
            if not empties[r, c]:
                continue
            if is_legal(you, opp, r, c):
                moves.append((r, c))
    return moves


def is_legal(you, opp, r, c):
    if you[r, c] or opp[r, c]:
        return False
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        found_opp = False
        while inside(rr, cc) and opp[rr, cc]:
            found_opp = True
            rr += dr
            cc += dc
        if found_opp and inside(rr, cc) and you[rr, cc]:
            return True
    return False


def apply_move(you, opp, move):
    r, c = move
    ny = you.copy()
    no = opp.copy()
    ny[r, c] = 1
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while inside(rr, cc) and no[rr, cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and inside(rr, cc) and ny[rr, cc]:
            for fr, fc in line:
                ny[fr, fc] = 1
                no[fr, fc] = 0
    return no, ny  # swap perspective: next player to move is opponent


def game_over(you, opp):
    if np.count_nonzero((you | opp) == 0) == 0:
        return True
    if legal_moves(you, opp):
        return False
    if legal_moves(opp, you):
        return False
    return True


def disc_diff(you, opp):
    return int(np.sum(you) - np.sum(opp))


def frontier_count(you, opp):
    occupied = (you | opp)
    frontier_you = 0
    frontier_opp = 0
    for r in range(8):
        for c in range(8):
            if not occupied[r, c]:
                continue
            frontier = False
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inside(rr, cc) and not occupied[rr, cc]:
                    frontier = True
                    break
            if frontier:
                if you[r, c]:
                    frontier_you += 1
                else:
                    frontier_opp += 1
    return frontier_you, frontier_opp


def corner_score(you, opp):
    ys = 0
    os = 0
    for r, c in CORNERS:
        if you[r, c]:
            ys += 1
        elif opp[r, c]:
            os += 1
    return ys - os


def corner_adjacency_score(you, opp):
    score = 0
    for sq, corner in X_SQUARES.items():
        sr, sc = sq
        cr, cc = corner
        if not you[cr, cc] and not opp[cr, cc]:
            if you[sr, sc]:
                score -= 1
            elif opp[sr, sc]:
                score += 1
    for sq, corner in C_SQUARES.items():
        sr, sc = sq
        cr, cc = corner
        if not you[cr, cc] and not opp[cr, cc]:
            if you[sr, sc]:
                score -= 1
            elif opp[sr, sc]:
                score += 1
    return score


def mobility_score(you, opp):
    mym = len(legal_moves(you, opp))
    opm = len(legal_moves(opp, you))
    return mym - opm, mym, opm


def potential_mobility(you, opp):
    occupied = (you | opp)
    my_pot = set()
    op_pot = set()
    for r in range(8):
        for c in range(8):
            if opp[r, c]:
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    if inside(rr, cc) and not occupied[rr, cc]:
                        my_pot.add((rr, cc))
            elif you[r, c]:
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    if inside(rr, cc) and not occupied[rr, cc]:
                        op_pot.add((rr, cc))
    return len(my_pot) - len(op_pot)


def edge_stability_hint(you, opp):
    score = 0
    for cr, cc in CORNERS:
        if you[cr, cc]:
            score += 1
            if cr == 0 and cc == 0:
                for c in range(1, 8):
                    if you[0, c]:
                        score += 0.2
                    else:
                        break
                for r in range(1, 8):
                    if you[r, 0]:
                        score += 0.2
                    else:
                        break
            elif cr == 0 and cc == 7:
                for c in range(6, -1, -1):
                    if you[0, c]:
                        score += 0.2
                    else:
                        break
                for r in range(1, 8):
                    if you[r, 7]:
                        score += 0.2
                    else:
                        break
            elif cr == 7 and cc == 0:
                for c in range(1, 8):
                    if you[7, c]:
                        score += 0.2
                    else:
                        break
                for r in range(6, -1, -1):
                    if you[r, 0]:
                        score += 0.2
                    else:
                        break
            else:
                for c in range(6, -1, -1):
                    if you[7, c]:
                        score += 0.2
                    else:
                        break
                for r in range(6, -1, -1):
                    if you[r, 7]:
                        score += 0.2
                    else:
                        break
        elif opp[cr, cc]:
            score -= 1
            if cr == 0 and cc == 0:
                for c in range(1, 8):
                    if opp[0, c]:
                        score -= 0.2
                    else:
                        break
                for r in range(1, 8):
                    if opp[r, 0]:
                        score -= 0.2
                    else:
                        break
            elif cr == 0 and cc == 7:
                for c in range(6, -1, -1):
                    if opp[0, c]:
                        score -= 0.2
                    else:
                        break
                for r in range(1, 8):
                    if opp[r, 7]:
                        score -= 0.2
                    else:
                        break
            elif cr == 7 and cc == 0:
                for c in range(1, 8):
                    if opp[7, c]:
                        score -= 0.2
                    else:
                        break
                for r in range(6, -1, -1):
                    if opp[r, 0]:
                        score -= 0.2
                    else:
                        break
            else:
                for c in range(6, -1, -1):
                    if opp[7, c]:
                        score -= 0.2
                    else:
                        break
                for r in range(6, -1, -1):
                    if opp[r, 7]:
                        score -= 0.2
                    else:
                        break
    return score


def evaluate(you, opp):
    empties = int(np.count_nonzero((you | opp) == 0))
    disc = int(np.sum(you) - np.sum(opp))
    pst = int(np.sum(PST * you) - np.sum(PST * opp))
    corners = corner_score(you, opp)
    adj = corner_adjacency_score(you, opp)
    mob, mym, opm = mobility_score(you, opp)
    potmob = potential_mobility(you, opp)
    fy, fo = frontier_count(you, opp)
    frontier = fo - fy
    stable_hint = edge_stability_hint(you, opp)

    if empties <= 10:
        return (
            1000 * disc +
            200 * corners +
            20 * mob +
            8 * pst +
            8 * frontier +
            10 * stable_hint +
            5 * potmob +
            20 * adj
        )

    if empties <= 24:
        return (
            15 * disc +
            250 * corners +
            14 * mob +
            10 * pst +
            12 * frontier +
            20 * stable_hint +
            6 * potmob +
            35 * adj
        )

    return (
        2 * disc +
        300 * corners +
        20 * mob +
        10 * pst +
        15 * frontier +
        20 * stable_hint +
        8 * potmob +
        40 * adj
    )


def terminal_value(you, opp):
    d = disc_diff(you, opp)
    if d > 0:
        return 100000 + d
    if d < 0:
        return -100000 + d
    return 0


def move_heuristic(you, opp, move):
    r, c = move
    score = PST[r, c] * 4

    if (r, c) in CORNERS:
        score += 10000

    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not you[cr, cc] and not opp[cr, cc]:
            score -= 3000

    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not you[cr, cc] and not opp[cr, cc]:
            score -= 1500

    # Estimate flips
    flips = 0
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        cnt = 0
        while inside(rr, cc) and opp[rr, cc]:
            cnt += 1
            rr += dr
            cc += dc
        if cnt and inside(rr, cc) and you[rr, cc]:
            flips += cnt
    score += flips * 15

    nopp, nyou = apply_move(you, opp, move)
    opp_moves = legal_moves(nopp, nyou)
    score -= len(opp_moves) * 40
    if len(opp_moves) == 0:
        score += 500

    return score


def ordered_moves(you, opp):
    moves = legal_moves(you, opp)
    moves.sort(key=lambda mv: move_heuristic(you, opp, mv), reverse=True)
    return moves


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.best_move = None
        self.timeout = False

    def check_time(self):
        if time.perf_counter() >= self.deadline:
            self.timeout = True
            raise TimeoutError

    def board_key(self, you, opp):
        return (you.tobytes(), opp.tobytes())

    def alphabeta(self, you, opp, depth, alpha, beta, passed=False):
        self.check_time()

        key = (self.board_key(you, opp), depth, passed)
        if key in self.tt:
            return self.tt[key]

        empties = int(np.count_nonzero((you | opp) == 0))
        moves = ordered_moves(you, opp)

        if depth == 0:
            val = evaluate(you, opp)
            self.tt[key] = val
            return val

        if not moves:
            opp_moves = legal_moves(opp, you)
            if not opp_moves:
                val = terminal_value(you, opp)
                self.tt[key] = val
                return val
            val = -self.alphabeta(opp, you, depth, -beta, -alpha, passed=True)
            self.tt[key] = val
            return val

        # Endgame exact extension
        if empties <= 8:
            depth = max(depth, empties + 2)

        value = -INF
        for mv in moves:
            nopp, nyou = apply_move(you, opp, mv)
            score = -self.alphabeta(nopp, nyou, depth - 1, -beta, -alpha, passed=False)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        self.tt[key] = value
        return value

    def search(self, you, opp):
        legal = legal_moves(you, opp)
        if not legal:
            return None
        if len(legal) == 1:
            return legal[0]

        # Quick tactical preference: corners first
        for mv in legal:
            if mv in CORNERS:
                return mv

        ordered = ordered_moves(you, opp)
        self.best_move = ordered[0]

        empties = int(np.count_nonzero((you | opp) == 0))
        if empties >= 44:
            max_depth = 4
        elif empties >= 28:
            max_depth = 5
        elif empties >= 16:
            max_depth = 7
        else:
            max_depth = min(12, empties + 2)

        for depth in range(2, max_depth + 1):
            self.check_time()
            best_val = -INF
            best_mv = self.best_move
            alpha = -INF
            beta = INF

            current_moves = ordered_moves(you, opp)
            if best_mv in current_moves:
                current_moves.remove(best_mv)
                current_moves = [best_mv] + current_moves

            for mv in current_moves:
                nopp, nyou = apply_move(you, opp, mv)
                score = -self.alphabeta(nopp, nyou, depth - 1, -beta, -alpha, passed=False)
                if score > best_val:
                    best_val = score
                    best_mv = mv
                if best_val > alpha:
                    alpha = best_val
            self.best_move = best_mv

        return self.best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you = np.asarray(you, dtype=np.uint8)
    opponent = np.asarray(opponent, dtype=np.uint8)

    legal = legal_moves(you, opponent)
    if not legal:
        return "pass"

    # Always keep a legal fallback
    fallback = ordered_moves(you, opponent)[0] if legal else legal[0]

    # Leave a little safety margin
    deadline = time.perf_counter() + 0.92
    searcher = Searcher(deadline)

    try:
        mv = searcher.search(you, opponent)
        if mv is None:
            return "pass"
        if mv in legal:
            return move_to_str(mv)
        return move_to_str(fallback)
    except Exception:
        # Any timeout or unexpected issue: still return a legal move
        return move_to_str(fallback)

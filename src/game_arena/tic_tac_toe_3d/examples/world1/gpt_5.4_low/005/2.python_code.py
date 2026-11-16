
from __future__ import annotations
import time
from functools import lru_cache

N = 3
ALL_CELLS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]

def idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k

def bit(i: int, j: int, k: int) -> int:
    return 1 << idx(i, j, k)

def generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append([idx(i, j, k) for i in range(3)])
    for i in range(3):
        for k in range(3):
            lines.append([idx(i, j, k) for j in range(3)])
    for i in range(3):
        for j in range(3):
            lines.append([idx(i, j, k) for k in range(3)])

    # Face diagonals in planes i fixed
    for i in range(3):
        lines.append([idx(i, 0, 0), idx(i, 1, 1), idx(i, 2, 2)])
        lines.append([idx(i, 0, 2), idx(i, 1, 1), idx(i, 2, 0)])

    # Face diagonals in planes j fixed
    for j in range(3):
        lines.append([idx(0, j, 0), idx(1, j, 1), idx(2, j, 2)])
        lines.append([idx(0, j, 2), idx(1, j, 1), idx(2, j, 0)])

    # Face diagonals in planes k fixed
    for k in range(3):
        lines.append([idx(0, 0, k), idx(1, 1, k), idx(2, 2, k)])
        lines.append([idx(0, 2, k), idx(1, 1, k), idx(2, 0, k)])

    # Space diagonals
    lines.append([idx(0, 0, 0), idx(1, 1, 1), idx(2, 2, 2)])
    lines.append([idx(0, 0, 2), idx(1, 1, 1), idx(2, 2, 0)])
    lines.append([idx(0, 2, 0), idx(1, 1, 1), idx(2, 0, 2)])
    lines.append([idx(0, 2, 2), idx(1, 1, 1), idx(2, 0, 0)])

    out = []
    seen = set()
    for line in lines:
        t = tuple(sorted(line))
        if t not in seen:
            seen.add(t)
            out.append(tuple(line))
    return out

LINES = generate_lines()
LINE_MASKS = [sum(1 << p for p in line) for line in LINES]
FULL_MASK = (1 << 27) - 1

CELL_TO_LINES = [[] for _ in range(27)]
for li, line in enumerate(LINES):
    for p in line:
        CELL_TO_LINES[p].append(li)

POS_WEIGHTS = [0] * 27
for i, j, k in ALL_CELLS:
    p = idx(i, j, k)
    POS_WEIGHTS[p] = len(CELL_TO_LINES[p]) * 3
    if (i, j, k) == (1, 1, 1):
        POS_WEIGHTS[p] += 12
    elif sum(v == 1 for v in (i, j, k)) == 2:
        POS_WEIGHTS[p] += 4

LINE_SCORE = [0, 2, 10, 1000000]

def bits_to_coord(p: int) -> tuple[int, int, int]:
    return (p // 9, (p % 9) // 3, p % 3)

def board_to_bits(board):
    my_bits = 0
    opp_bits = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                b = bit(i, j, k)
                if v == 1:
                    my_bits |= b
                elif v == -1:
                    opp_bits |= b
    return my_bits, opp_bits

def legal_positions(my_bits: int, opp_bits: int):
    occ = my_bits | opp_bits
    empties = []
    x = (~occ) & FULL_MASK
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        empties.append(p)
        x ^= lsb
    return empties

def has_win(bits_: int) -> bool:
    for m in LINE_MASKS:
        if (bits_ & m) == m:
            return True
    return False

def immediate_winning_positions(my_bits: int, opp_bits: int):
    occ = my_bits | opp_bits
    wins = []
    x = (~occ) & FULL_MASK
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        if has_win(my_bits | lsb):
            wins.append(p)
        x ^= lsb
    return wins

def count_immediate_wins(my_bits: int, opp_bits: int) -> int:
    return len(immediate_winning_positions(my_bits, opp_bits))

def heuristic(my_bits: int, opp_bits: int) -> int:
    if has_win(my_bits):
        return 10000000
    if has_win(opp_bits):
        return -10000000

    score = 0

    my_wins = count_immediate_wins(my_bits, opp_bits)
    opp_wins = count_immediate_wins(opp_bits, my_bits)
    score += 5000 * my_wins
    score -= 5500 * opp_wins

    for lm in LINE_MASKS:
        a = (my_bits & lm).bit_count()
        b = (opp_bits & lm).bit_count()
        if a and b:
            continue
        if a:
            score += LINE_SCORE[a]
        elif b:
            score -= LINE_SCORE[b]

    occupied = my_bits | opp_bits
    x = occupied
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        if my_bits & lsb:
            score += POS_WEIGHTS[p]
        else:
            score -= POS_WEIGHTS[p]
        x ^= lsb

    return score

def ordered_moves(my_bits: int, opp_bits: int):
    empties = legal_positions(my_bits, opp_bits)

    opp_immediate = set(immediate_winning_positions(opp_bits, my_bits))
    out = []

    for p in empties:
        pb = 1 << p
        score = POS_WEIGHTS[p]

        if has_win(my_bits | pb):
            score += 1000000

        if p in opp_immediate:
            score += 200000

        new_my = my_bits | pb
        my_forks = count_immediate_wins(new_my, opp_bits)
        score += 15000 * my_forks

        opp_after = count_immediate_wins(opp_bits, new_my)
        score -= 18000 * opp_after

        for li in CELL_TO_LINES[p]:
            lm = LINE_MASKS[li]
            a = (new_my & lm).bit_count()
            b = (opp_bits & lm).bit_count()
            if not (a and b):
                if a:
                    score += [0, 3, 20, 0][a]
                elif b:
                    score -= [0, 3, 20, 0][b]

        out.append((score, p))

    out.sort(reverse=True)
    return [p for _, p in out]

def choose_tactical(my_bits: int, opp_bits: int):
    legal = legal_positions(my_bits, opp_bits)
    if not legal:
        return None

    wins = immediate_winning_positions(my_bits, opp_bits)
    if wins:
        wins.sort(key=lambda p: POS_WEIGHTS[p], reverse=True)
        return wins[0]

    opp_wins = immediate_winning_positions(opp_bits, my_bits)
    if opp_wins:
        blockers = []
        opp_wins_set = set(opp_wins)
        for p in legal:
            pb = 1 << p
            val = 0
            if p in opp_wins_set:
                val += 100000
            if has_win(my_bits | pb):
                val += 1000000
            val += 12000 * count_immediate_wins(my_bits | pb, opp_bits)
            val -= 15000 * count_immediate_wins(opp_bits, my_bits | pb)
            val += POS_WEIGHTS[p]
            blockers.append((val, p))
        blockers.sort(reverse=True)
        return blockers[0][1]

    best = None
    bestv = -10**18
    for p in legal:
        pb = 1 << p
        my_forks = count_immediate_wins(my_bits | pb, opp_bits)
        opp_forks = count_immediate_wins(opp_bits, my_bits | pb)
        v = 20000 * my_forks - 22000 * opp_forks + POS_WEIGHTS[p]
        if v > bestv:
            bestv = v
            best = p
    return best

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = time.perf_counter()
    time_limit = 0.92

    try:
        my_bits, opp_bits = board_to_bits(board)
        legal = legal_positions(my_bits, opp_bits)
        if not legal:
            return (0, 0, 0)

        tactical = choose_tactical(my_bits, opp_bits)
        if tactical is not None:
            pb = 1 << tactical
            if has_win(my_bits | pb):
                return bits_to_coord(tactical)

        empties = len(legal)
        if empties <= 8:
            max_depth = empties
        elif empties <= 12:
            max_depth = 6
        elif empties <= 16:
            max_depth = 5
        else:
            max_depth = 4

        TT = {}

        def negamax(cur_my: int, cur_opp: int, depth: int, alpha: int, beta: int) -> int:
            key = (cur_my, cur_opp, depth, alpha, beta)
            if key in TT:
                return TT[key]

            if has_win(cur_opp):
                return -9000000 - depth

            empties_local = legal_positions(cur_my, cur_opp)
            if not empties_local:
                return 0

            if depth == 0 or (time.perf_counter() - start) > time_limit:
                v = heuristic(cur_my, cur_opp)
                TT[key] = v
                return v

            wins = immediate_winning_positions(cur_my, cur_opp)
            if wins:
                return 8000000 + depth

            opp_wins = immediate_winning_positions(cur_opp, cur_my)

            best = -10**18
            moves = ordered_moves(cur_my, cur_opp)

            if opp_wins:
                opp_wins_set = set(opp_wins)
                forced = [p for p in moves if p in opp_wins_set or has_win(cur_my | (1 << p))]
                if forced:
                    moves = forced

            for p in moves:
                pb = 1 << p
                score = -negamax(cur_opp, cur_my | pb, depth - 1, -beta, -alpha)
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break

            TT[key] = best
            return best

        best_move = tactical if tactical is not None else legal[0]
        best_score = -10**18

        moves = ordered_moves(my_bits, opp_bits)
        if tactical is not None and tactical in moves:
            moves.remove(tactical)
            moves = [tactical] + moves

        for p in moves:
            if (time.perf_counter() - start) > time_limit:
                break
            pb = 1 << p
            if has_win(my_bits | pb):
                return bits_to_coord(p)
            score = -negamax(opp_bits, my_bits | pb, max_depth - 1, -10**18, 10**18)
            score += POS_WEIGHTS[p]
            if score > best_score:
                best_score = score
                best_move = p

        coord = bits_to_coord(best_move)
        if board[coord[0]][coord[1]][coord[2]] == 0:
            return coord

    except Exception:
        pass

    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    return (0, 0, 0)


from __future__ import annotations
import time

ROW0 = 0xFF
ROW7 = 0xFF << 56
INF = 10**9

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    def bit_of(r: int, c: int) -> int:
        return 1 << (r * 8 + c)

    def bits_from_positions(ps: list[tuple[int, int]]) -> int:
        b = 0
        for r, c in ps:
            b |= bit_of(r, c)
        return b

    if color == 'w':
        white = bits_from_positions(me)
        black = bits_from_positions(opp)
    else:
        white = bits_from_positions(opp)
        black = bits_from_positions(me)

    deadline = time.perf_counter() + 0.93
    node_counter = [0]
    tt: dict[tuple[int, int, str, int], int] = {}

    def iter_bits(bb: int):
        while bb:
            lsb = bb & -bb
            idx = lsb.bit_length() - 1
            yield idx
            bb ^= lsb

    def idx_to_rc(idx: int) -> tuple[int, int]:
        return (idx >> 3, idx & 7)

    def generate_moves(w: int, b: int, stm: str):
        occ = w | b
        own = w if stm == 'w' else b
        oppb = b if stm == 'w' else w
        dr = 1 if stm == 'w' else -1
        goal_row = 7 if stm == 'w' else 0
        moves = []

        for frm in iter_bits(own):
            r = frm >> 3
            c = frm & 7
            nr = r + dr
            if nr < 0 or nr > 7:
                continue

            to = nr * 8 + c
            to_bit = 1 << to
            if not (occ & to_bit):
                score = 0
                if nr == goal_row:
                    score += 1_000_000
                score += 20
                score += (nr * 8 if stm == 'w' else (7 - nr) * 8)
                score += 3 - abs(3.5 - c)
                moves.append((score, frm, to, False))

            nc = c - 1
            if nc >= 0:
                to = nr * 8 + nc
                to_bit = 1 << to
                if not (own & to_bit):
                    cap = bool(oppb & to_bit)
                    score = 0
                    if nr == goal_row:
                        score += 1_000_000
                    if cap:
                        score += 5000
                    else:
                        score += 10
                    score += (nr * 8 if stm == 'w' else (7 - nr) * 8)
                    score += 3 - abs(3.5 - nc)
                    moves.append((score, frm, to, cap))

            nc = c + 1
            if nc <= 7:
                to = nr * 8 + nc
                to_bit = 1 << to
                if not (own & to_bit):
                    cap = bool(oppb & to_bit)
                    score = 0
                    if nr == goal_row:
                        score += 1_000_000
                    if cap:
                        score += 5000
                    else:
                        score += 10
                    score += (nr * 8 if stm == 'w' else (7 - nr) * 8)
                    score += 3 - abs(3.5 - nc)
                    moves.append((score, frm, to, cap))

        moves.sort(reverse=True)
        return moves

    def make_move(w: int, b: int, stm: str, frm: int, to: int):
        frm_bit = 1 << frm
        to_bit = 1 << to
        if stm == 'w':
            w = (w ^ frm_bit) | to_bit
            if b & to_bit:
                b ^= to_bit
        else:
            b = (b ^ frm_bit) | to_bit
            if w & to_bit:
                w ^= to_bit
        return w, b

    def is_terminal(w: int, b: int):
        if w & ROW7:
            return True, 1
        if b & ROW0:
            return True, -1
        if b == 0:
            return True, 1
        if w == 0:
            return True, -1
        return False, 0

    def eval_white(w: int, b: int) -> int:
        term, res = is_terminal(w, b)
        if term:
            return INF if res > 0 else -INF

        score = 0
        wc = w.bit_count()
        bc = b.bit_count()
        score += 220 * (wc - bc)

        for idx in iter_bits(w):
            r = idx >> 3
            c = idx & 7
            score += 18 * r
            if r == 6:
                score += 500
            elif r == 5:
                score += 150

            blocked = False
            rr = r + 1
            while rr <= 7:
                hit = False
                for cc in (c - 1, c, c + 1):
                    if 0 <= cc <= 7 and (b & (1 << (rr * 8 + cc))):
                        hit = True
                        break
                if hit:
                    blocked = True
                    break
                rr += 1
            if not blocked:
                score += 80 + 18 * r

            support = 0
            br = r - 1
            if br >= 0:
                if c - 1 >= 0 and (w & (1 << (br * 8 + c - 1))):
                    support += 1
                if c + 1 <= 7 and (w & (1 << (br * 8 + c + 1))):
                    support += 1
            score += 22 * support
            score += int(6 - abs(3.5 - c) * 2)

        for idx in iter_bits(b):
            r = idx >> 3
            c = idx & 7
            score -= 18 * (7 - r)
            if r == 1:
                score -= 500
            elif r == 2:
                score -= 150

            blocked = False
            rr = r - 1
            while rr >= 0:
                hit = False
                for cc in (c - 1, c, c + 1):
                    if 0 <= cc <= 7 and (w & (1 << (rr * 8 + cc))):
                        hit = True
                        break
                if hit:
                    blocked = True
                    break
                rr -= 1
            if not blocked:
                score -= 80 + 18 * (7 - r)

            support = 0
            br = r + 1
            if br <= 7:
                if c - 1 >= 0 and (b & (1 << (br * 8 + c - 1))):
                    support += 1
                if c + 1 <= 7 and (b & (1 << (br * 8 + c + 1))):
                    support += 1
            score -= 22 * support
            score -= int(6 - abs(3.5 - c) * 2)

        return score

    def maybe_timeout():
        node_counter[0] += 1
        if (node_counter[0] & 1023) == 0 and time.perf_counter() > deadline:
            raise TimeoutError

    def negamax(w: int, b: int, stm: str, depth: int, alpha: int, beta: int) -> int:
        maybe_timeout()

        term, res = is_terminal(w, b)
        if term:
            if res > 0:
                return INF if stm == 'w' else -INF
            return INF if stm == 'b' else -INF

        if depth == 0:
            v = eval_white(w, b)
            return v if stm == 'w' else -v

        key = (w, b, stm, depth)
        if key in tt:
            return tt[key]

        moves = generate_moves(w, b, stm)
        if not moves:
            return -INF + 1

        best = -INF
        next_stm = 'b' if stm == 'w' else 'w'
        for _, frm, to, _ in moves:
            nw, nb = make_move(w, b, stm, frm, to)
            score = -negamax(nw, nb, next_stm, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    stm = color
    root_moves = generate_moves(white, black, stm)

    if not root_moves:
        if color == 'w':
            return ((0, 0), (0, 0))
        return ((7, 0), (7, 0))

    best_move = root_moves[0]
    best_pair = (idx_to_rc(best_move[1]), idx_to_rc(best_move[2]))

    for _, frm, to, _ in root_moves:
        nr = to >> 3
        if (color == 'w' and nr == 7) or (color == 'b' and nr == 0):
            return (idx_to_rc(frm), idx_to_rc(to))

    try:
        depth = 1
        while depth <= 5:
            current_best_score = -INF
            current_best_move = best_move
            alpha = -INF
            beta = INF
            next_stm = 'b' if stm == 'w' else 'w'

            ordered = generate_moves(white, black, stm)
            for _, frm, to, _ in ordered:
                nw, nb = make_move(white, black, stm, frm, to)
                score = -negamax(nw, nb, next_stm, depth - 1, -beta, -alpha)
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = (_, frm, to, False)
                    best_pair = (idx_to_rc(frm), idx_to_rc(to))
                if score > alpha:
                    alpha = score
            best_move = current_best_move
            depth += 1
    except TimeoutError:
        pass

    return best_pair

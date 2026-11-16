
import time

MATE = 10**8

ROW_MASKS = tuple(0xFF << (8 * r) for r in range(8))
WHITE_GOAL_MASK = ROW_MASKS[7]
BLACK_GOAL_MASK = ROW_MASKS[0]

FILE_A = sum(1 << (8 * r) for r in range(8))
FILE_H = sum(1 << (8 * r + 7) for r in range(8))

ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]

CENTER_BONUS = [0, 2, 4, 6, 6, 4, 2, 0]
ADV_BONUS = [0, 8, 18, 32, 52, 78, 115, 0]


def other(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def bits_from_list(pieces):
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def decode_move(move):
    s, t = move
    return ((s >> 3, s & 7), (t >> 3, t & 7))


class Search:
    __slots__ = ("deadline", "tt", "nodes")

    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.perf_counter() >= self.deadline:
            raise TimeoutError

    @staticmethod
    def winner(white, black):
        if (white & WHITE_GOAL_MASK) or black == 0:
            return 'w'
        if (black & BLACK_GOAL_MASK) or white == 0:
            return 'b'
        return None

    @staticmethod
    def white_attacks(white):
        return ((white & ~FILE_A) << 7) | ((white & ~FILE_H) << 9)

    @staticmethod
    def black_attacks(black):
        return ((black & ~FILE_A) >> 9) | ((black & ~FILE_H) >> 7)

    @staticmethod
    def count_promotion_moves(white, black, color):
        occ = white | black
        if color == 'w':
            w6 = white & ROW_MASKS[6]
            return (
                (((w6 << 8) & ~occ & WHITE_GOAL_MASK).bit_count())
                + ((((w6 & ~FILE_A) << 7) & ~white & WHITE_GOAL_MASK).bit_count())
                + ((((w6 & ~FILE_H) << 9) & ~white & WHITE_GOAL_MASK).bit_count())
            )
        else:
            b1 = black & ROW_MASKS[1]
            return (
                (((b1 >> 8) & ~occ & BLACK_GOAL_MASK).bit_count())
                + ((((b1 & ~FILE_A) >> 9) & ~black & BLACK_GOAL_MASK).bit_count())
                + ((((b1 & ~FILE_H) >> 7) & ~black & BLACK_GOAL_MASK).bit_count())
            )

    @staticmethod
    def is_winning_move(move, color):
        _, t = move
        r = t >> 3
        return (color == 'w' and r == 7) or (color == 'b' and r == 0)

    @staticmethod
    def apply_move(white, black, color, move):
        s, t = move
        fb = 1 << s
        tb = 1 << t
        if color == 'w':
            white = (white ^ fb) | tb
            if black & tb:
                black ^= tb
        else:
            black = (black ^ fb) | tb
            if white & tb:
                white ^= tb
        return white, black

    @staticmethod
    def generate_moves(white, black, color):
        moves = []
        occ = white | black
        if color == 'w':
            my = white
            bb = my
            while bb:
                lsb = bb & -bb
                s = lsb.bit_length() - 1
                bb ^= lsb
                r = s >> 3
                c = s & 7
                if r == 7:
                    continue
                t = s + 8
                if not (occ & (1 << t)):
                    moves.append((s, t))
                if c > 0:
                    t = s + 7
                    if not (my & (1 << t)):
                        moves.append((s, t))
                if c < 7:
                    t = s + 9
                    if not (my & (1 << t)):
                        moves.append((s, t))
        else:
            my = black
            bb = my
            while bb:
                lsb = bb & -bb
                s = lsb.bit_length() - 1
                bb ^= lsb
                r = s >> 3
                c = s & 7
                if r == 0:
                    continue
                t = s - 8
                if not (occ & (1 << t)):
                    moves.append((s, t))
                if c > 0:
                    t = s - 9
                    if not (my & (1 << t)):
                        moves.append((s, t))
                if c < 7:
                    t = s - 7
                    if not (my & (1 << t)):
                        moves.append((s, t))
        return moves

    def evaluate_white(self, white, black):
        if (white & WHITE_GOAL_MASK) or black == 0:
            return MATE
        if (black & BLACK_GOAL_MASK) or white == 0:
            return -MATE

        w_count = white.bit_count()
        b_count = black.bit_count()

        w_att = self.white_attacks(white)
        b_att = self.black_attacks(black)

        score = 125 * (w_count - b_count)

        w_best = 0
        b_best = 0

        bb = white
        while bb:
            lsb = bb & -bb
            s = lsb.bit_length() - 1
            bb ^= lsb
            bit = 1 << s
            r = ROW[s]
            c = COL[s]
            prog = r
            if prog > w_best:
                w_best = prog

            score += ADV_BONUS[prog]
            score += CENTER_BONUS[c] * 3

            defended = bool(bit & w_att)
            attacked = bool(bit & b_att)

            if defended:
                score += 8
            if attacked:
                if defended:
                    score -= 8
                else:
                    score -= 28 + 7 * prog
            elif prog >= 4:
                score += 10 * prog

            if c > 0 and (white & (1 << (s - 1))):
                score += 4
            if c < 7 and (white & (1 << (s + 1))):
                score += 4

        bb = black
        while bb:
            lsb = bb & -bb
            s = lsb.bit_length() - 1
            bb ^= lsb
            bit = 1 << s
            r = ROW[s]
            c = COL[s]
            prog = 7 - r
            if prog > b_best:
                b_best = prog

            score -= ADV_BONUS[prog]
            score -= CENTER_BONUS[c] * 3

            defended = bool(bit & b_att)
            attacked = bool(bit & w_att)

            if defended:
                score -= 8
            if attacked:
                if defended:
                    score += 8
                else:
                    score += 28 + 7 * prog
            elif prog >= 4:
                score -= 10 * prog

            if c > 0 and (black & (1 << (s - 1))):
                score -= 4
            if c < 7 and (black & (1 << (s + 1))):
                score -= 4

        score += 45 * (w_best - b_best)

        w_prom = self.count_promotion_moves(white, black, 'w')
        b_prom = self.count_promotion_moves(white, black, 'b')
        score += 4200 * (w_prom - b_prom)

        return score

    def evaluate(self, white, black, color):
        score = self.evaluate_white(white, black)
        return score if color == 'w' else -score

    def order_moves(self, white, black, color, moves, tt_move=None):
        if len(moves) <= 1:
            return moves

        opp_att = self.black_attacks(black) if color == 'w' else self.white_attacks(white)
        my_att = self.white_attacks(white) if color == 'w' else self.black_attacks(black)
        opp_bits = black if color == 'w' else white

        scored = []
        for m in moves:
            s, t = m
            sb = 1 << s
            tb = 1 << t
            tr = t >> 3
            tc = t & 7

            sc = 0
            if tt_move is not None and m == tt_move:
                sc += 10_000_000

            if self.is_winning_move(m, color):
                sc += 9_000_000

            if opp_bits & tb:
                if color == 'w':
                    victim_prog = 7 - tr
                else:
                    victim_prog = tr
                sc += 400_000 + 5000 * victim_prog

            from_prog = (s >> 3) if color == 'w' else (7 - (s >> 3))
            to_prog = tr if color == 'w' else (7 - tr)
            sc += (to_prog - from_prog) * 3000
            sc += to_prog * 200
            sc += CENTER_BONUS[tc] * 50

            if tb & my_att:
                sc += 250
            if not (tb & opp_att):
                sc += 600
            elif (sb & opp_att) and not (tb & opp_att):
                sc += 250

            scored.append((sc, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def negamax(self, white, black, color, depth, alpha, beta, ply):
        self.check_time()

        win = self.winner(white, black)
        if win is not None:
            return (MATE - ply) if win == color else (-MATE + ply)

        if depth == 0:
            my_now = self.count_promotion_moves(white, black, color)
            if my_now:
                return MATE // 2 - ply
            opp_now = self.count_promotion_moves(white, black, other(color))
            if opp_now:
                return -MATE // 2 + ply
            return self.evaluate(white, black, color)

        key = (white, black, color)
        alpha_orig = alpha
        beta_orig = beta
        tt_move = None

        entry = self.tt.get(key)
        if entry is not None:
            e_depth, e_score, e_flag, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_score
                elif e_flag == 1:
                    if e_score > alpha:
                        alpha = e_score
                else:
                    if e_score < beta:
                        beta = e_score
                if alpha >= beta:
                    return e_score

        moves = self.generate_moves(white, black, color)
        if not moves:
            return -MATE + ply

        moves = self.order_moves(white, black, color, moves, tt_move)

        best_score = -MATE
        best_move = moves[0]

        next_color = other(color)

        for m in moves:
            w2, b2 = self.apply_move(white, black, color, m)
            score = -self.negamax(w2, b2, next_color, depth - 1, -beta, -alpha, ply + 1)

            if score > best_score:
                best_score = score
                best_move = m
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        if best_score <= alpha_orig:
            flag = 2
        elif best_score >= beta_orig:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best_score, flag, best_move)

        return best_score

    def search_root(self, white, black, color, depth, pv_move=None):
        self.check_time()

        moves = self.generate_moves(white, black, color)
        if not moves:
            return -MATE, None

        entry = self.tt.get((white, black, color))
        tt_move = entry[3] if entry is not None else None
        if pv_move is not None:
            tt_move = pv_move

        moves = self.order_moves(white, black, color, moves, tt_move)

        alpha = -MATE
        beta = MATE
        best_score = -MATE
        best_move = moves[0]
        next_color = other(color)

        for m in moves:
            self.check_time()
            w2, b2 = self.apply_move(white, black, color, m)
            score = -self.negamax(w2, b2, next_color, depth - 1, -beta, -alpha, 1)

            if score > best_score:
                best_score = score
                best_move = m
            if score > alpha:
                alpha = score

        self.tt[(white, black, color)] = (depth, best_score, 0, best_move)
        return best_score, best_move


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if color == 'w':
        white = bits_from_list(me)
        black = bits_from_list(opp)
    else:
        black = bits_from_list(me)
        white = bits_from_list(opp)

    deadline = time.perf_counter() + 0.93
    search = Search(deadline)

    moves = search.generate_moves(white, black, color)
    if not moves:
        # Should not happen in a valid non-terminal position.
        # Return something deterministic if forced.
        p = me[0]
        return (p, p)

    ordered = search.order_moves(white, black, color, moves, None)
    best_move = ordered[0]

    for m in ordered:
        if search.is_winning_move(m, color):
            return decode_move(m)

    opp_color = other(color)
    if search.count_promotion_moves(white, black, opp_color):
        safe = []
        for m in ordered:
            w2, b2 = search.apply_move(white, black, color, m)
            if search.winner(w2, b2) == color or search.count_promotion_moves(w2, b2, opp_color) == 0:
                safe.append(m)
        if safe:
            best_move = safe[0]

    total_pieces = white.bit_count() + black.bit_count()
    if total_pieces <= 8:
        max_depth = 7
    elif total_pieces <= 12:
        max_depth = 6
    elif total_pieces <= 20:
        max_depth = 5
    else:
        max_depth = 4

    if search.count_promotion_moves(white, black, color) or search.count_promotion_moves(white, black, opp_color):
        max_depth += 1

    pv_move = best_move
    for depth in range(1, max_depth + 1):
        try:
            _, move = search.search_root(white, black, color, depth, pv_move)
            if move is not None:
                best_move = move
                pv_move = move
        except TimeoutError:
            break

    return decode_move(best_move)

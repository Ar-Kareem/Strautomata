
from __future__ import annotations

from time import perf_counter


# 64-bit board helpers ---------------------------------------------------------

FULL_MASK = (1 << 64) - 1
ROW_MASKS = [0xFF << (8 * r) for r in range(8)]
FILE_A = sum(1 << (8 * r) for r in range(8))
FILE_H = FILE_A << 7
NOT_FILE_A = FULL_MASK ^ FILE_A
NOT_FILE_H = FULL_MASK ^ FILE_H

WIN_SCORE = 100_000_000
INF = 1_000_000_000

EXACT, LOWER, UPPER = 0, 1, 2

# Piece-square / evaluation tuning
ADV_PS = [0, 18, 52, 110, 210, 380, 720, 0]
CENTER_BONUS = [0, 4, 10, 14, 14, 10, 4, 0]
FREE_RUN = [0, 0, 18, 40, 75, 130, 220, 0]

ROW_OF = [sq >> 3 for sq in range(64)]
COL_OF = [sq & 7 for sq in range(64)]
COORDS = [(ROW_OF[sq], COL_OF[sq]) for sq in range(64)]

ADV_WHITE_SQ = [ROW_OF[sq] for sq in range(64)]
ADV_BLACK_SQ = [7 - ROW_OF[sq] for sq in range(64)]

W_SQ = [ADV_PS[ADV_WHITE_SQ[sq]] + CENTER_BONUS[COL_OF[sq]] for sq in range(64)]
B_SQ = [ADV_PS[ADV_BLACK_SQ[sq]] + CENTER_BONUS[COL_OF[sq]] for sq in range(64)]

# Precomputed masks:
# FRONT3_W[sq]: all squares ahead of white piece in same / adjacent files
# FRONT3_B[sq]: same for black
# BLACK_CAPTURERS[dst]: black source squares that could capture a white piece on dst
# WHITE_CAPTURERS[dst]: white source squares that could capture a black piece on dst
FRONT3_W = [0] * 64
FRONT3_B = [0] * 64
BLACK_CAPTURERS = [0] * 64
WHITE_CAPTURERS = [0] * 64

for sq in range(64):
    r = ROW_OF[sq]
    c = COL_OF[sq]

    mask = 0
    for rr in range(r + 1, 8):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                mask |= 1 << (rr * 8 + cc)
    FRONT3_W[sq] = mask

    mask = 0
    for rr in range(r):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                mask |= 1 << (rr * 8 + cc)
    FRONT3_B[sq] = mask

    mask = 0
    if r < 7:
        if c > 0:
            mask |= 1 << ((r + 1) * 8 + (c - 1))
        if c < 7:
            mask |= 1 << ((r + 1) * 8 + (c + 1))
    BLACK_CAPTURERS[sq] = mask

    mask = 0
    if r > 0:
        if c > 0:
            mask |= 1 << ((r - 1) * 8 + (c - 1))
        if c < 7:
            mask |= 1 << ((r - 1) * 8 + (c + 1))
    WHITE_CAPTURERS[sq] = mask


def pieces_to_bb(pieces: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def white_attacks_mask(white: int) -> int:
    return ((((white & NOT_FILE_A) << 7) | ((white & NOT_FILE_H) << 9)) & FULL_MASK)


def black_attacks_mask(black: int) -> int:
    return (((black & NOT_FILE_A) >> 9) | ((black & NOT_FILE_H) >> 7))


def move_code(move: tuple[int, int, bool]) -> int:
    return (move[0] << 6) | move[1]


class SearchTimeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline: float):
        self.deadline = deadline
        self.nodes = 0
        self.tt: dict[tuple[int, int, bool], tuple[int, int, int, int | None]] = {}
        self.history = [0] * 4096
        self.killers = [[-1, -1] for _ in range(128)]

    def check_time(self) -> None:
        self.nodes += 1
        if (self.nodes & 255) == 0 and perf_counter() >= self.deadline:
            raise SearchTimeout

    def gen_moves(
        self, white: int, black: int, white_to_move: bool
    ) -> list[tuple[int, int, bool]]:
        moves: list[tuple[int, int, bool]] = []
        occ = white | black

        if white_to_move:
            own = white
            opp = black
            bb = white
            while bb:
                lsb = bb & -bb
                src = lsb.bit_length() - 1
                bb ^= lsb

                r = ROW_OF[src]
                c = COL_OF[src]
                if r == 7:
                    continue

                dst = src + 8
                if ((occ >> dst) & 1) == 0:
                    moves.append((src, dst, False))

                if c > 0:
                    dst = src + 7
                    if ((own >> dst) & 1) == 0:
                        moves.append((src, dst, ((opp >> dst) & 1) != 0))

                if c < 7:
                    dst = src + 9
                    if ((own >> dst) & 1) == 0:
                        moves.append((src, dst, ((opp >> dst) & 1) != 0))
        else:
            own = black
            opp = white
            bb = black
            while bb:
                lsb = bb & -bb
                src = lsb.bit_length() - 1
                bb ^= lsb

                r = ROW_OF[src]
                c = COL_OF[src]
                if r == 0:
                    continue

                dst = src - 8
                if ((occ >> dst) & 1) == 0:
                    moves.append((src, dst, False))

                if c > 0:
                    dst = src - 9
                    if ((own >> dst) & 1) == 0:
                        moves.append((src, dst, ((opp >> dst) & 1) != 0))

                if c < 7:
                    dst = src - 7
                    if ((own >> dst) & 1) == 0:
                        moves.append((src, dst, ((opp >> dst) & 1) != 0))

        return moves

    def apply_move(
        self, white: int, black: int, white_to_move: bool, move: tuple[int, int, bool]
    ) -> tuple[int, int]:
        src, dst, cap = move
        from_mask = 1 << src
        to_mask = 1 << dst

        if white_to_move:
            white = (white ^ from_mask) | to_mask
            if cap:
                black &= ~to_mask
        else:
            black = (black ^ from_mask) | to_mask
            if cap:
                white &= ~to_mask

        return white, black

    def dest_capturable(self, dst: int, white_to_move: bool, opp: int) -> bool:
        if white_to_move:
            return (opp & BLACK_CAPTURERS[dst]) != 0
        return (opp & WHITE_CAPTURERS[dst]) != 0

    def score_move(
        self,
        move: tuple[int, int, bool],
        opp: int,
        white_to_move: bool,
        ply: int,
        tt_code: int | None,
        opp_count: int,
        opp_threat_mask: int,
    ) -> int:
        code = move_code(move)
        if tt_code is not None and code == tt_code:
            return 2_000_000_000

        score = self.history[code]
        if ply < len(self.killers):
            if code == self.killers[ply][0]:
                score += 9000
            elif code == self.killers[ply][1]:
                score += 8000

        src, dst, cap = move
        r = ROW_OF[dst]
        c = COL_OF[dst]
        adv = r if white_to_move else 7 - r

        if white_to_move:
            if r == 7:
                score += 1_000_000
            elif r == 6:
                score += 50_000
        else:
            if r == 0:
                score += 1_000_000
            elif r == 1:
                score += 50_000

        if cap:
            score += 25_000
            enemy_adv = (7 - r) if white_to_move else r
            score += 300 * enemy_adv
            if opp_count == 1:
                score += 900_000

        if opp_threat_mask:
            if cap and ((1 << dst) & opp_threat_mask):
                score += 500_000
            else:
                score -= 120_000

        score += 120 * adv + CENTER_BONUS[c] * 10

        if self.dest_capturable(dst, white_to_move, opp):
            score -= 70
        else:
            score += 50

        return score

    def order_moves(
        self,
        moves: list[tuple[int, int, bool]],
        white: int,
        black: int,
        white_to_move: bool,
        ply: int,
        tt_code: int | None,
    ) -> list[tuple[int, int, bool]]:
        opp = black if white_to_move else white
        opp_count = opp.bit_count()
        opp_threat_mask = (black & ROW_MASKS[1]) if white_to_move else (white & ROW_MASKS[6])

        scored = []
        for m in moves:
            scored.append(
                (
                    self.score_move(m, opp, white_to_move, ply, tt_code, opp_count, opp_threat_mask),
                    m,
                )
            )
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def evaluate(self, white: int, black: int, white_to_move: bool) -> int:
        wc = white.bit_count()
        bc = black.bit_count()

        white_att = white_attacks_mask(white)
        black_att = black_attacks_mask(black)

        supported_w = (white & white_att).bit_count()
        supported_b = (black & black_att).bit_count()

        strong_w = (white & white_att & (~black_att)).bit_count()
        strong_b = (black & black_att & (~white_att)).bit_count()

        vuln_w = (white & black_att).bit_count()
        vuln_b = (black & white_att).bit_count()

        occ = white | black
        empty = FULL_MASK ^ occ
        not_white = FULL_MASK ^ white
        not_black = FULL_MASK ^ black

        wm = (
            (((white << 8) & FULL_MASK & empty).bit_count())
            + ((((white & NOT_FILE_A) << 7) & FULL_MASK & not_white).bit_count())
            + ((((white & NOT_FILE_H) << 9) & FULL_MASK & not_white).bit_count())
        )
        bm = (
            (((black >> 8) & empty).bit_count())
            + ((((black & NOT_FILE_A) >> 9) & not_black).bit_count())
            + ((((black & NOT_FILE_H) >> 7) & not_black).bit_count())
        )

        wpos = 0
        bpos = 0
        maxw = 0
        maxb = 0
        freew = 0
        freeb = 0

        bb = white
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            adv = ADV_WHITE_SQ[sq]
            wpos += W_SQ[sq]
            if adv > maxw:
                maxw = adv
            if (black & FRONT3_W[sq]) == 0:
                freew += FREE_RUN[adv]

        bb = black
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            adv = ADV_BLACK_SQ[sq]
            bpos += B_SQ[sq]
            if adv > maxb:
                maxb = adv
            if (white & FRONT3_B[sq]) == 0:
                freeb += FREE_RUN[adv]

        row6_w = (white & ROW_MASKS[6]).bit_count()
        row5_w = (white & ROW_MASKS[5]).bit_count()
        row1_b = (black & ROW_MASKS[1]).bit_count()
        row2_b = (black & ROW_MASKS[2]).bit_count()

        score = 260 * (wc - bc)
        score += (wpos - bpos)
        score += 45 * (maxw - maxb)
        score += (freew - freeb)
        score += 20 * (supported_w - supported_b)
        score += 12 * (strong_w - strong_b)
        score -= 28 * (vuln_w - vuln_b)
        score += 6 * (wm - bm)
        score += 260 * (row6_w - row1_b)
        score += 80 * (row5_w - row2_b)

        return score if white_to_move else -score

    def note_cutoff(self, ply: int, code: int, depth: int) -> None:
        if ply < len(self.killers):
            if code != self.killers[ply][0]:
                self.killers[ply][1] = self.killers[ply][0]
                self.killers[ply][0] = code
        self.history[code] += depth * depth

    def search(
        self,
        white: int,
        black: int,
        white_to_move: bool,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> int:
        self.check_time()

        # Terminal positions
        if (white & ROW_MASKS[7]) or black == 0:
            return (WIN_SCORE - ply) if white_to_move else (-WIN_SCORE + ply)
        if (black & ROW_MASKS[0]) or white == 0:
            return (-WIN_SCORE + ply) if white_to_move else (WIN_SCORE - ply)

        # Immediate win in one move
        if white_to_move:
            if white & ROW_MASKS[6]:
                return WIN_SCORE - ply - 1
            if black.bit_count() == 1 and (black & white_attacks_mask(white)):
                return WIN_SCORE - ply - 1
        else:
            if black & ROW_MASKS[1]:
                return WIN_SCORE - ply - 1
            if white.bit_count() == 1 and (white & black_attacks_mask(black)):
                return WIN_SCORE - ply - 1

        # Resolve promotion-race tactics one ply deeper
        if depth <= 0:
            if (white & ROW_MASKS[6]) or (black & ROW_MASKS[1]):
                depth = 1
            else:
                return self.evaluate(white, black, white_to_move)

        key = (white, black, white_to_move)
        orig_alpha = alpha
        orig_beta = beta

        tt_entry = self.tt.get(key)
        tt_move_code = None
        if tt_entry is not None:
            tt_depth, tt_flag, tt_value, tt_move_code = tt_entry
            if tt_depth >= depth:
                if tt_flag == EXACT:
                    return tt_value
                if tt_flag == LOWER and tt_value > alpha:
                    alpha = tt_value
                elif tt_flag == UPPER and tt_value < beta:
                    beta = tt_value
                if alpha >= beta:
                    return tt_value

        moves = self.gen_moves(white, black, white_to_move)
        if not moves:
            return -WIN_SCORE + ply

        moves = self.order_moves(moves, white, black, white_to_move, ply, tt_move_code)

        best_value = -INF
        best_code = None
        critical = bool((white & ROW_MASKS[6]) or (black & ROW_MASKS[1]))

        for idx, move in enumerate(moves):
            nwhite, nblack = self.apply_move(white, black, white_to_move, move)
            dst_row = ROW_OF[move[1]]
            interesting = move[2] or (white_to_move and dst_row >= 6) or ((not white_to_move) and dst_row <= 1)

            reduction = 0
            if depth >= 4 and idx >= 4 and (not interesting) and (not critical):
                reduction = 1

            if idx == 0:
                value = -self.search(
                    nwhite, nblack, not white_to_move, depth - 1, -beta, -alpha, ply + 1
                )
            else:
                value = -self.search(
                    nwhite,
                    nblack,
                    not white_to_move,
                    depth - 1 - reduction,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )
                if reduction and value > alpha:
                    value = -self.search(
                        nwhite, nblack, not white_to_move, depth - 1, -alpha - 1, -alpha, ply + 1
                    )
                if value > alpha and value < beta:
                    value = -self.search(
                        nwhite, nblack, not white_to_move, depth - 1, -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_code = move_code(move)

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not interesting:
                    self.note_cutoff(ply, move_code(move), depth)
                break

        if best_value <= orig_alpha:
            flag = UPPER
        elif best_value >= orig_beta:
            flag = LOWER
        else:
            flag = EXACT
        self.tt[key] = (depth, flag, best_value, best_code)

        return best_value

    def root_search(
        self,
        white: int,
        black: int,
        white_to_move: bool,
        depth: int,
        root_moves: list[tuple[int, int, bool]],
        hint_code: int | None,
    ) -> tuple[int, tuple[int, int, bool] | None]:
        self.check_time()

        tt_entry = self.tt.get((white, black, white_to_move))
        tt_code = hint_code if hint_code is not None else (tt_entry[3] if tt_entry is not None else None)

        moves = self.order_moves(root_moves, white, black, white_to_move, 0, tt_code)
        alpha = -INF
        beta = INF

        best_value = -INF
        best_move = moves[0] if moves else None

        for idx, move in enumerate(moves):
            self.check_time()
            nwhite, nblack = self.apply_move(white, black, white_to_move, move)

            if idx == 0:
                value = -self.search(
                    nwhite, nblack, not white_to_move, depth - 1, -beta, -alpha, 1
                )
            else:
                value = -self.search(
                    nwhite, nblack, not white_to_move, depth - 1, -alpha - 1, -alpha, 1
                )
                if value > alpha and value < beta:
                    value = -self.search(
                        nwhite, nblack, not white_to_move, depth - 1, -beta, -alpha, 1
                    )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

        if best_move is not None:
            self.tt[(white, black, white_to_move)] = (
                depth,
                EXACT,
                best_value,
                move_code(best_move),
            )

        return best_value, best_move

    def find_best(
        self, white: int, black: int, white_to_move: bool
    ) -> tuple[int, int, bool] | None:
        moves = self.gen_moves(white, black, white_to_move)
        if not moves:
            return None

        opp_count = black.bit_count() if white_to_move else white.bit_count()

        # Immediate winning move?
        for m in moves:
            dst_row = ROW_OF[m[1]]
            if white_to_move:
                if dst_row == 7 or (m[2] and opp_count == 1):
                    return m
            else:
                if dst_row == 0 or (m[2] and opp_count == 1):
                    return m

        # If opponent has exactly one immediate promotion threat, capturing it is mandatory
        opp_threat_mask = (black & ROW_MASKS[1]) if white_to_move else (white & ROW_MASKS[6])
        if opp_threat_mask.bit_count() == 1:
            forced = [m for m in moves if m[2] and ((1 << m[1]) & opp_threat_mask)]
            if forced:
                moves = forced

        if len(moves) == 1:
            return moves[0]

        moves = self.order_moves(moves, white, black, white_to_move, 0, None)
        best = moves[0]
        best_code = move_code(best)

        for depth in range(1, 33):
            if perf_counter() >= self.deadline:
                break
            try:
                value, candidate = self.root_search(
                    white, black, white_to_move, depth, moves, best_code
                )
                if candidate is not None:
                    best = candidate
                    best_code = move_code(candidate)
                if value >= WIN_SCORE // 2:
                    break
            except SearchTimeout:
                break

        return best


def emergency_legal_move(
    me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    me_set = set(me)
    occ = me_set | set(opp)
    dr = 1 if color == "w" else -1

    for r, c in me:
        nr = r + dr
        if not (0 <= nr < 8):
            continue

        # forward: only if empty
        if (nr, c) not in occ:
            return ((r, c), (nr, c))

        # diagonal: legal if not occupied by own piece
        if c > 0 and (nr, c - 1) not in me_set:
            return ((r, c), (nr, c - 1))
        if c < 7 and (nr, c + 1) not in me_set:
            return ((r, c), (nr, c + 1))

    # Unreachable in a valid non-terminal position, but keep a total fallback.
    if me:
        return (me[0], me[0])
    return ((0, 0), (0, 0))


def policy(
    me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        white_to_move = color == "w"
        if white_to_move:
            white = pieces_to_bb(me)
            black = pieces_to_bb(opp)
        else:
            white = pieces_to_bb(opp)
            black = pieces_to_bb(me)

        searcher = Searcher(perf_counter() + 0.93)
        best = searcher.find_best(white, black, white_to_move)
        if best is not None:
            return COORDS[best[0]], COORDS[best[1]]
    except Exception:
        pass

    return emergency_legal_move(me, opp, color)


from __future__ import annotations

from functools import lru_cache
from time import perf_counter

BLACK = 0
WHITE = 1

WIN = 1_000_000_000
INF = 2_000_000_000

EXACT = 0
LOWER = 1
UPPER = 2

BOTTOM_ROW_MASK = 0xFF
TOP_ROW_MASK = 0xFF << 56

GOAL_MASK = [BOTTOM_ROW_MASK, TOP_ROW_MASK]          # black -> row 0, white -> row 7
PENULT_MASK = [0xFF << 8, 0xFF << 48]               # black -> row 1, white -> row 6

DESTS = [[() for _ in range(64)] for _ in range(2)]
PROTECT_MASK = [[0] * 64 for _ in range(2)]
ATTACK_MASK = [[0] * 64 for _ in range(2)]
PROGRESS = [[0] * 64 for _ in range(2)]
CENTER = [0] * 64

_center_col = [0, 1, 2, 3, 3, 2, 1, 0]

for idx in range(64):
    r, c = divmod(idx, 8)

    CENTER[idx] = _center_col[c]
    PROGRESS[WHITE][idx] = r
    PROGRESS[BLACK][idx] = 7 - r

    # White moves upward: +8, +7, +9
    if r < 7:
        d = [idx + 8]
        if c > 0:
            d.append(idx + 7)
        if c < 7:
            d.append(idx + 9)
        DESTS[WHITE][idx] = tuple(d)

    # Black moves downward: -8, -9, -7
    if r > 0:
        d = [idx - 8]
        if c > 0:
            d.append(idx - 9)
        if c < 7:
            d.append(idx - 7)
        DESTS[BLACK][idx] = tuple(d)

    # White piece at idx is protected by white pieces behind it.
    m = 0
    if r > 0 and c > 0:
        m |= 1 << (idx - 9)
    if r > 0 and c < 7:
        m |= 1 << (idx - 7)
    PROTECT_MASK[WHITE][idx] = m

    # Black attackers of a white piece at idx.
    m = 0
    if r < 7 and c > 0:
        m |= 1 << (idx + 7)
    if r < 7 and c < 7:
        m |= 1 << (idx + 9)
    ATTACK_MASK[WHITE][idx] = m

    # Black piece at idx is protected by black pieces behind it.
    m = 0
    if r < 7 and c > 0:
        m |= 1 << (idx + 7)
    if r < 7 and c < 7:
        m |= 1 << (idx + 9)
    PROTECT_MASK[BLACK][idx] = m

    # White attackers of a black piece at idx.
    m = 0
    if r > 0 and c > 0:
        m |= 1 << (idx - 9)
    if r > 0 and c < 7:
        m |= 1 << (idx - 7)
    ATTACK_MASK[BLACK][idx] = m


class SearchTimeout(Exception):
    pass


def _bb_from_coords(pieces: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def _idx_to_coord(idx: int) -> tuple[int, int]:
    return (idx >> 3, idx & 7)


@lru_cache(maxsize=100000)
def _free_runner_stats(own_bb: int, side: int) -> tuple[int, int]:
    """
    Static path-to-goal estimate ignoring opponent pieces as blockers
    (they can be captured diagonally), but treating own pieces as blockers.
    Returns (best_progress_with_path, count_of_pieces_with_path).
    """
    rows = [((own_bb >> (8 * r)) & 0xFF) for r in range(8)]
    count = 0
    best = -1

    if side == WHITE:
        accessible = (~rows[7]) & 0xFF
        for r in range(6, -1, -1):
            source = accessible | ((accessible << 1) & 0xFF) | (accessible >> 1)
            piece_mask = rows[r] & source
            if piece_mask:
                count += piece_mask.bit_count()
                if r > best:
                    best = r
            accessible = source & ((~rows[r]) & 0xFF)
    else:
        accessible = (~rows[0]) & 0xFF
        for r in range(1, 8):
            source = accessible | ((accessible << 1) & 0xFF) | (accessible >> 1)
            piece_mask = rows[r] & source
            if piece_mask:
                count += piece_mask.bit_count()
                p = 7 - r
                if p > best:
                    best = p
            accessible = source & ((~rows[r]) & 0xFF)

    return best, count


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    side = WHITE if color == "w" else BLACK
    other = 1 - side

    me_bb = _bb_from_coords(me)
    opp_bb = _bb_from_coords(opp)

    deadline = perf_counter() + 0.93

    TT: dict[tuple[int, int, int], tuple[int, int, int, tuple[int, int] | None]] = {}
    HISTORY: dict[tuple[int, int, int], int] = {}
    node_count = 0

    def count_legal_moves(meb: int, oppb: int, s: int) -> int:
        occ = meb | oppb
        n = 0
        bb = meb
        while bb:
            lsb = bb & -bb
            idx = lsb.bit_length() - 1
            bb ^= lsb
            dests = DESTS[s][idx]
            if not dests:
                continue

            to = dests[0]
            if not (occ & (1 << to)):
                n += 1

            for to in dests[1:]:
                if not (meb & (1 << to)):
                    n += 1
        return n

    def evaluate(meb: int, oppb: int, s: int) -> int:
        o = 1 - s
        my_count = meb.bit_count()
        opp_count = oppb.bit_count()

        score = 64 * (my_count - opp_count)

        my_sum = 0
        my_best = 0
        my_prot = 0
        my_cent = 0
        my_threat = 0

        bb = meb
        while bb:
            lsb = bb & -bb
            idx = lsb.bit_length() - 1
            bb ^= lsb

            p = PROGRESS[s][idx]
            my_sum += p
            if p > my_best:
                my_best = p
            my_cent += CENTER[idx]

            prot = 1 if (PROTECT_MASK[s][idx] & meb) else 0
            if prot:
                my_prot += 1 + (p // 2)

            attackers = ATTACK_MASK[s][idx] & oppb
            if attackers:
                my_threat += (1 + p) if not prot else (p // 2)

        opp_sum = 0
        opp_best = 0
        opp_prot = 0
        opp_cent = 0
        opp_threat = 0

        bb = oppb
        while bb:
            lsb = bb & -bb
            idx = lsb.bit_length() - 1
            bb ^= lsb

            p = PROGRESS[o][idx]
            opp_sum += p
            if p > opp_best:
                opp_best = p
            opp_cent += CENTER[idx]

            prot = 1 if (PROTECT_MASK[o][idx] & oppb) else 0
            if prot:
                opp_prot += 1 + (p // 2)

            attackers = ATTACK_MASK[o][idx] & meb
            if attackers:
                opp_threat += (1 + p) if not prot else (p // 2)

        my_free_best, my_free_count = _free_runner_stats(meb, s)
        opp_free_best, opp_free_count = _free_runner_stats(oppb, o)

        score += 12 * (my_sum - opp_sum)
        score += 28 * (my_best - opp_best)
        score += 36 * (my_free_best - opp_free_best)
        score += 8 * (my_free_count - opp_free_count)
        score += 4 * (my_prot - opp_prot)
        score += 7 * (opp_threat - my_threat)
        score += 2 * (my_cent - opp_cent)

        if my_count + opp_count <= 10:
            score += 2 * (
                count_legal_moves(meb, oppb, s) -
                count_legal_moves(oppb, meb, o)
            )

        return score

    def generate_ordered_moves(
        meb: int,
        oppb: int,
        s: int,
        tt_move: tuple[int, int] | None = None,
        force_capture_mask: int = 0,
    ) -> list[tuple[int, int, int]]:
        occ = meb | oppb
        goal_mask = GOAL_MASK[s]
        own_penult = PENULT_MASK[s]
        opp_penult = oppb & PENULT_MASK[1 - s]

        moves_scored: list[tuple[int, int, int, int]] = []

        bb = meb
        while bb:
            from_bit = bb & -bb
            frm = from_bit.bit_length() - 1
            bb ^= from_bit

            dests = DESTS[s][frm]
            if not dests:
                continue

            # Forward move: only to empty square.
            if not force_capture_mask:
                to = dests[0]
                to_bit = 1 << to
                if not (occ & to_bit):
                    score = HISTORY.get((s, frm, to), 0)
                    if tt_move == (frm, to):
                        score += 2_000_000
                    if to_bit & goal_mask:
                        score += 1_500_000
                    if to_bit & own_penult:
                        score += 25_000
                    score += 900 * PROGRESS[s][to] + 20 * CENTER[to]

                    new_me = (meb ^ from_bit) | to_bit
                    if PROTECT_MASK[s][to] & new_me:
                        score += 150
                    if ATTACK_MASK[s][to] & oppb:
                        score -= 100

                    moves_scored.append((score, frm, to, 0))

            # Diagonal moves: empty or capture opponent.
            for to in dests[1:]:
                to_bit = 1 << to
                if meb & to_bit:
                    continue

                cap = 1 if (oppb & to_bit) else 0
                if force_capture_mask and not (cap and (to_bit & force_capture_mask)):
                    continue

                score = HISTORY.get((s, frm, to), 0)
                if tt_move == (frm, to):
                    score += 2_000_000
                if to_bit & goal_mask:
                    score += 1_500_000
                if cap:
                    if oppb == to_bit:
                        score += 1_400_000
                    score += 60_000 + 2_000 * PROGRESS[1 - s][to]
                    if to_bit & opp_penult:
                        score += 900_000
                if to_bit & own_penult:
                    score += 25_000
                score += 900 * PROGRESS[s][to] + 20 * CENTER[to]

                new_me = (meb ^ from_bit) | to_bit
                if PROTECT_MASK[s][to] & new_me:
                    score += 150
                if ATTACK_MASK[s][to] & oppb:
                    score -= 100

                moves_scored.append((score, frm, to, cap))

        moves_scored.sort(reverse=True)
        return [(frm, to, cap) for _, frm, to, cap in moves_scored]

    def negamax(meb: int, oppb: int, s: int, depth: int, alpha: int, beta: int, ply: int) -> int:
        nonlocal node_count
        node_count += 1
        if (node_count & 1023) == 0 and perf_counter() >= deadline:
            raise SearchTimeout

        o = 1 - s

        # Terminal positions.
        if oppb == 0:
            return WIN - ply
        if meb == 0:
            return -WIN + ply
        if meb & GOAL_MASK[s]:
            return WIN - ply
        if oppb & GOAL_MASK[o]:
            return -WIN + ply

        # Exact one-move wins.
        if meb & PENULT_MASK[s]:
            return WIN - (ply + 1)

        if oppb and not (oppb & (oppb - 1)):
            target_idx = oppb.bit_length() - 1
            if ATTACK_MASK[o][target_idx] & meb:
                return WIN - (ply + 1)

        # Exact tactical threat handling:
        # If opponent has a penultimate-row piece, it wins next turn unless captured now.
        force_capture_mask = 0
        opp_threat_mask = oppb & PENULT_MASK[o]
        if opp_threat_mask:
            if opp_threat_mask.bit_count() > 1:
                return -WIN + (ply + 2)
            force_capture_mask = opp_threat_mask

        tt_depth = depth if depth > 0 else 0
        key = (meb, oppb, s)
        tt_move = None

        entry = TT.get(key)
        if entry is not None:
            edepth, flag, escore, emove = entry
            tt_move = emove
            if edepth >= tt_depth:
                if flag == EXACT:
                    return escore
                if flag == LOWER:
                    if escore > alpha:
                        alpha = escore
                else:
                    if escore < beta:
                        beta = escore
                if alpha >= beta:
                    return escore

        if depth <= 0 and not force_capture_mask:
            return evaluate(meb, oppb, s)

        alpha_orig = alpha
        beta_orig = beta

        moves = generate_ordered_moves(meb, oppb, s, tt_move, force_capture_mask)
        if not moves:
            if force_capture_mask:
                return -WIN + (ply + 2)
            return -WIN + ply

        best = -INF
        best_move: tuple[int, int] | None = None
        goal_mask = GOAL_MASK[s]

        for frm, to, _cap in moves:
            from_bit = 1 << frm
            to_bit = 1 << to

            next_me = oppb & ~to_bit
            my_after = (meb ^ from_bit) | to_bit

            if (to_bit & goal_mask) or next_me == 0:
                score = WIN - (ply + 1)
            else:
                score = -negamax(next_me, my_after, o, depth - 1, -beta, -alpha, ply + 1)

            if score > best:
                best = score
                best_move = (frm, to)

            if best > alpha:
                alpha = best
            if alpha >= beta:
                HISTORY[(s, frm, to)] = HISTORY.get((s, frm, to), 0) + max(1, depth) * max(1, depth)
                break

        flag = EXACT
        if best <= alpha_orig:
            flag = UPPER
        elif best >= beta_orig:
            flag = LOWER

        TT[key] = (tt_depth, flag, best, best_move)
        return best

    def search_root(depth: int) -> tuple[int, tuple[int, int] | None]:
        root_key = (me_bb, opp_bb, side)
        root_entry = TT.get(root_key)
        tt_move = root_entry[3] if root_entry is not None else None

        opp_threat_mask = opp_bb & PENULT_MASK[other]
        if opp_threat_mask and not (me_bb & PENULT_MASK[side]) and opp_threat_mask.bit_count() == 1:
            moves = generate_ordered_moves(me_bb, opp_bb, side, tt_move, opp_threat_mask)
            if not moves:
                moves = generate_ordered_moves(me_bb, opp_bb, side, tt_move, 0)
        else:
            moves = generate_ordered_moves(me_bb, opp_bb, side, tt_move, 0)

        if not moves:
            return -WIN, None

        best_score = -INF
        best_move = (moves[0][0], moves[0][1])

        alpha = -INF
        beta = INF
        goal_mask = GOAL_MASK[side]

        for frm, to, _cap in moves:
            if perf_counter() >= deadline:
                raise SearchTimeout

            from_bit = 1 << frm
            to_bit = 1 << to

            next_me = opp_bb & ~to_bit
            my_after = (me_bb ^ from_bit) | to_bit

            if (to_bit & goal_mask) or next_me == 0:
                score = WIN - 1
            else:
                score = -negamax(next_me, my_after, other, depth - 1, -beta, -alpha, 1)

            if score > best_score:
                best_score = score
                best_move = (frm, to)

            if best_score > alpha:
                alpha = best_score

        TT[root_key] = (depth, EXACT, best_score, best_move)
        return best_score, best_move

    # Fallback move generation.
    all_moves = generate_ordered_moves(me_bb, opp_bb, side, None, 0)

    # If no move exists, the position should already be terminal.
    # Best effort fallback.
    if not all_moves:
        if me:
            fr = me[0]
            return (fr, fr)
        return ((0, 0), (0, 0))

    # Immediate winning move: reach goal row or capture last opponent piece.
    opp_count = opp_bb.bit_count()
    for frm, to, cap in all_moves:
        to_bit = 1 << to
        if (to_bit & GOAL_MASK[side]) or (cap and opp_count == 1):
            return (_idx_to_coord(frm), _idx_to_coord(to))

    fallback_move = (all_moves[0][0], all_moves[0][1])

    # If there is exactly one urgent penultimate-row threat and only one saving capture, just play it.
    opp_threat_mask = opp_bb & PENULT_MASK[other]
    if opp_threat_mask and not (me_bb & PENULT_MASK[side]) and opp_threat_mask.bit_count() == 1:
        forced = generate_ordered_moves(me_bb, opp_bb, side, None, opp_threat_mask)
        if forced:
            fallback_move = (forced[0][0], forced[0][1])
            if len(forced) == 1:
                return (_idx_to_coord(fallback_move[0]), _idx_to_coord(fallback_move[1]))

    if len(all_moves) == 1:
        return (_idx_to_coord(fallback_move[0]), _idx_to_coord(fallback_move[1]))

    best_move = fallback_move

    max_depth = 10
    for depth in range(1, max_depth + 1):
        try:
            score, move = search_root(depth)
            if move is not None:
                best_move = move
            if score > WIN // 2:
                break
        except SearchTimeout:
            break

    return (_idx_to_coord(best_move[0]), _idx_to_coord(best_move[1]))

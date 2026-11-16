
import time

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

RANK = tuple(255 << (8 * r) for r in range(8))
GOAL = (RANK[7], RANK[0])
PENULT = (RANK[6], RANK[1])
TWO_AWAY = (RANK[5], RANK[2])
ADVANCED = (
    RANK[3] | RANK[4] | RANK[5],
    RANK[2] | RANK[3] | RANK[4],
)

MATE = 100000
MATE_BOUND = 90000
INF = 1000000

ADV = (0, 5, 14, 28, 50, 85, 180, 0)
CENTER = (0, 2, 4, 5, 5, 4, 2, 0)
RESERVE = (0, 16, 29, 38, 43, 45, 45, 45, 45)
PASS_BONUS = (0, 0, 0, 38, 90, 180, 0, 0)

# Positional evaluation of each possible occupied rank.
COUNTS = tuple(x.bit_count() for x in range(256))
CENTER_SUM = tuple(
    sum(CENTER[c] for c in range(8) if x & (1 << c))
    for x in range(256)
)

PST = []
for side in range(2):
    rows = []
    for r in range(8):
        progress = r if side == 0 else 7 - r
        rows.append(tuple(
            (100 + ADV[progress]) * COUNTS[x]
            + (CENTER_SUM[x] if progress < 5 else CENTER_SUM[x] // 2)
            for x in range(256)
        ))
    PST.append(tuple(rows))
PST = tuple(PST)

# REVERSE_ATTACK[s][t]: squares from which side s can capture t.
# INTERCEPT conservatively contains every enemy that could obstruct
# or capture a pawn running straight toward promotion.
REVERSE_ATTACK = [[0] * 64 for _ in range(2)]
INTERCEPT = [[0] * 64 for _ in range(2)]
FORWARD_FILE = [[0] * 64 for _ in range(2)]

for side in range(2):
    direction = 1 if side == 0 else -1
    for square in range(64):
        r, c = divmod(square, 8)

        source_row = r - direction
        if 0 <= source_row < 8:
            for source_col in (c - 1, c + 1):
                if 0 <= source_col < 8:
                    REVERSE_ATTACK[side][square] |= (
                        1 << (8 * source_row + source_col)
                    )

        rr = r + direction
        distance = 1
        while 0 <= rr < 8:
            FORWARD_FILE[side][square] |= 1 << (8 * rr + c)
            radius = (distance + 1) // 2
            for cc in range(max(0, c - radius), min(8, c + radius + 1)):
                INTERCEPT[side][square] |= 1 << (8 * rr + cc)
            rr += direction
            distance += 1


def _attacks(pieces, side):
    if side == 0:
        return (
            ((pieces & NOT_A) << 7)
            | ((pieces & NOT_H) << 9)
        ) & FULL
    return (
        ((pieces & NOT_A) >> 9)
        | ((pieces & NOT_H) >> 7)
    )


def _forward(pieces, side):
    return ((pieces << 8) & FULL) if side == 0 else (pieces >> 8)


def _moves(pieces, enemies, side):
    """Moves encoded as source * 64 + destination."""
    result = []
    occupied = pieces | enemies

    if side == 0:
        groups = (
            (((pieces << 8) & FULL) & ~occupied, 8),
            (((pieces & NOT_A) << 7) & FULL & ~pieces, 7),
            (((pieces & NOT_H) << 9) & FULL & ~pieces, 9),
        )
    else:
        groups = (
            ((pieces >> 8) & ~occupied, -8),
            (((pieces & NOT_A) >> 9) & ~pieces, -9),
            (((pieces & NOT_H) >> 7) & ~pieces, -7),
        )

    for targets, delta in groups:
        while targets:
            bit = targets & -targets
            targets ^= bit
            destination = bit.bit_length() - 1
            source = destination - delta
            result.append((source << 6) | destination)
    return result


def _safe_penultimate(pieces, enemies, side, enemy_attacks):
    sources = pieces & TWO_AWAY[side]
    if not sources:
        return 0
    targets = (
        (_attacks(sources, side) & ~pieces)
        | (_forward(sources, side) & ~(pieces | enemies))
    )
    return targets & ~enemy_attacks & FULL


def _forced_captures(pieces, threat, side):
    destination = threat.bit_length() - 1
    sources = REVERSE_ATTACK[side][destination] & pieces
    result = []
    while sources:
        bit = sources & -sources
        sources ^= bit
        result.append(((bit.bit_length() - 1) << 6) | destination)
    return result


def _pack_score(value, ply):
    if value > MATE_BOUND:
        return value + ply
    if value < -MATE_BOUND:
        return value - ply
    return value


def _unpack_score(value, ply):
    if value > MATE_BOUND:
        return value - ply
    if value < -MATE_BOUND:
        return value + ply
    return value


class _SearchTimeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.history = [[0] * 4096 for _ in range(2)]
        self.killers = [[-1, -1] for _ in range(128)]

    def evaluate(self, p, q, side, pa, qa, ply):
        other = side ^ 1
        score = 0
        pp, qq = p, q
        pt, qt = PST[side], PST[other]

        for r in range(8):
            score += pt[r][pp & 255] - qt[r][qq & 255]
            pp >>= 8
            qq >>= 8

        # Diagonal support and adjacent pawn formations.
        score += 7 * ((p & pa).bit_count() - (q & qa).bit_count())
        score += 5 * (
            (p & ((p & NOT_H) << 1)).bit_count()
            - (q & ((q & NOT_H) << 1)).bit_count()
        )

        # The player to move has more opportunity to rescue attacked pawns.
        ph = p & qa & ~pa
        qh = q & pa & ~qa
        score -= 15 * ph.bit_count()
        score += 29 * qh.bit_count()
        score -= 5 * (p & qa & pa).bit_count()
        score += 8 * (q & pa & qa).bit_count()
        score -= 18 * (ph & TWO_AWAY[side]).bit_count()
        score += 25 * (qh & TWO_AWAY[other]).bit_count()

        empty = FULL ^ (p | q)
        pm = ((pa & ~p) | (_forward(p, side) & empty)) & ~qa
        qm = ((qa & ~q) | (_forward(q, other) & empty)) & ~pa
        score += 2 * (pm.bit_count() - qm.bit_count())
        score += 7 * (
            (pm & TWO_AWAY[side]).bit_count()
            - (qm & TWO_AWAY[other]).bit_count()
        )

        # A few home-rank defenders are valuable; a full idle back rank is not.
        if side == 0:
            home_p = p & 255
            home_q = (q >> 56) & 255
            p_min = 7 - ((p.bit_length() - 1) >> 3)
            q_min = ((q & -q).bit_length() - 1) >> 3
        else:
            home_p = (p >> 56) & 255
            home_q = q & 255
            p_min = ((p & -p).bit_length() - 1) >> 3
            q_min = 7 - ((q.bit_length() - 1) >> 3)

        score += RESERVE[home_p.bit_count()] - RESERVE[home_q.bit_count()]

        p_free = 9
        q_free = 9
        candidates = p & ADVANCED[side]
        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            square = bit.bit_length() - 1
            if not (q & INTERCEPT[side][square]):
                progress = square >> 3
                if side:
                    progress = 7 - progress
                if not (p & FORWARD_FILE[side][square]):
                    distance = 7 - progress
                    if distance < p_free:
                        p_free = distance
                    score += PASS_BONUS[progress]
                else:
                    score += PASS_BONUS[progress] // 4

        candidates = q & ADVANCED[other]
        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            square = bit.bit_length() - 1
            if not (p & INTERCEPT[other][square]):
                progress = square >> 3
                if other:
                    progress = 7 - progress
                if not (q & FORWARD_FILE[other][square]):
                    distance = 7 - progress
                    if distance < q_free:
                        q_free = distance
                    score -= PASS_BONUS[progress]
                else:
                    score -= PASS_BONUS[progress] // 4

        # Proven races: the runner cannot be intercepted, and even the
        # opponent's most advanced pawn cannot arrive sooner.
        if p_free <= q_min:
            return MATE - ply - (2 * p_free - 1)
        if q_free < p_min:
            return -MATE + ply + 2 * q_free

        return score + 8

    def ordered(self, moves, p, q, side, qa, tt_move, ply):
        killers = self.killers[min(ply, 127)]
        history = self.history[side]
        result = []

        for move in moves:
            if move == tt_move:
                result.append((10000000, move))
                continue

            source = move >> 6
            target = move & 63
            source_bit = 1 << source
            target_bit = 1 << target
            progress = target >> 3
            old_progress = source >> 3
            if side:
                progress = 7 - progress
                old_progress = 7 - old_progress

            score = 6 * (ADV[progress] - ADV[old_progress])
            score += CENTER[target & 7] - CENTER[source & 7]

            if target_bit & q:
                score += 6500 + 12 * ADV[7 - progress]
            else:
                score += history[move]
                if move == killers[0]:
                    score += 4500
                elif move == killers[1]:
                    score += 3500

            if progress == 6:
                score += 24000
            elif progress == 5:
                score += 650

            if target_bit & qa:
                supported = REVERSE_ATTACK[side][target] & (p ^ source_bit)
                score -= 1400 if supported else 3200
            elif source_bit & qa:
                score += 550

            result.append((score, move))

        result.sort(reverse=True)
        return [move for _, move in result]

    def search(self, p, q, side, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 127) == 0:
            if time.perf_counter() >= self.deadline:
                raise _SearchTimeout

        other = side ^ 1
        if not p or (q & GOAL[other]):
            return -MATE + ply
        if not q or (p & GOAL[side]):
            return MATE - ply

        # A pawn on its penultimate rank always has a winning diagonal.
        if p & PENULT[side]:
            return MATE - ply - 1

        threat = q & PENULT[other]
        forced = bool(threat)
        moves = None

        if forced:
            if threat & (threat - 1):
                return -MATE + ply + 2
            moves = _forced_captures(p, threat, side)
            if not moves:
                return -MATE + ply + 2

        qa = _attacks(q, other)
        pa = _attacks(p, side)

        if not forced and _safe_penultimate(p, q, side, qa):
            return MATE - ply - 3

        key = (p, q, side)
        entry = self.tt.get(key)
        tt_move = -1

        if entry is not None:
            stored_depth, stored_value, flag, tt_move = entry
            if stored_depth >= max(depth, 0):
                value = _unpack_score(stored_value, ply)
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        original_alpha = alpha
        danger = (
            not forced
            and bool(_safe_penultimate(q, p, other, pa))
        )
        best = -INF
        best_move = -1

        if depth <= 0 and not forced:
            stand = self.evaluate(p, q, side, pa, qa, ply)
            if abs(stand) > MATE_BOUND:
                return stand

            if depth <= -3:
                return stand - (160 if danger else 0)

            if not danger:
                best = stand
                if stand >= beta:
                    return stand
                if stand > alpha:
                    alpha = stand

            moves = _moves(p, q, side)
            if not danger:
                # Captures and promotion threats form the quiescence search.
                noisy_targets = q | PENULT[side]
                moves = [
                    move for move in moves
                    if (1 << (move & 63)) & noisy_targets
                ]

        if moves is None:
            moves = _moves(p, q, side)

        if not moves:
            if depth <= 0 and not forced and not danger:
                return best
            return -MATE + ply

        moves = self.ordered(moves, p, q, side, qa, tt_move, ply)

        for index, move in enumerate(moves):
            source = move >> 6
            target = move & 63
            source_bit = 1 << source
            target_bit = 1 << target
            capture = bool(q & target_bit)

            new_p = (p ^ source_bit) | target_bit
            new_q = q & ~target_bit
            next_depth = depth - 1

            if index == 0 or depth <= 0:
                value = -self.search(
                    new_q, new_p, other, next_depth,
                    -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                progress = target >> 3
                if side:
                    progress = 7 - progress

                if (
                    depth >= 3 and index >= 4 and ply > 0
                    and not capture and not forced and not danger
                    and progress < 5 and not (source_bit & qa)
                    and move != tt_move
                ):
                    reduction = 1
                    if depth >= 6 and index >= 12:
                        reduction = 2

                value = -self.search(
                    new_q, new_p, other, next_depth - reduction,
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and value > alpha:
                    value = -self.search(
                        new_q, new_p, other, next_depth,
                        -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -self.search(
                        new_q, new_p, other, next_depth,
                        -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if depth > 0 and not capture:
                    killers = self.killers[min(ply, 127)]
                    if killers[0] != move:
                        killers[1] = killers[0]
                        killers[0] = move

                    history = self.history[side]
                    bonus = min(400, 18 * depth * depth)
                    old = history[move]
                    history[move] = old + bonus - old * bonus // 5000
                break

        if depth > 0:
            if best <= original_alpha:
                flag = 2
            elif best >= beta:
                flag = 1
            else:
                flag = 0
            self.tt[key] = (
                depth, _pack_score(best, ply), flag, best_move
            )

        return best


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    started = time.perf_counter()

    # Reflect black's position vertically so the root player always moves up.
    reflect = color == 'b'
    p = 0
    q = 0

    for r, c in me:
        if reflect:
            r = 7 - r
        p |= 1 << (8 * r + c)

    for r, c in opp:
        if reflect:
            r = 7 - r
        q |= 1 << (8 * r + c)

    def decode(move):
        source, target = move >> 6, move & 63
        fr, fc = divmod(source, 8)
        tr, tc = divmod(target, 8)
        if reflect:
            fr = 7 - fr
            tr = 7 - tr
        return ((fr, fc), (tr, tc))

    legal = _moves(p, q, 0)

    # Arena calls are assumed to be nonterminal, hence legal is nonempty.
    # Establish a legal fallback before starting any search.
    fallback = legal[0]

    for move in legal:
        target_bit = 1 << (move & 63)
        if target_bit & GOAL[0] or not (q & ~target_bit):
            return decode(move)

    if len(legal) == 1:
        return decode(fallback)

    engine = _Engine(started + 0.90)
    qa = _attacks(q, 1)
    ordered = engine.ordered(legal, p, q, 0, qa, -1, 0)
    fallback = ordered[0]

    threat = q & PENULT[1]
    if threat:
        if threat & (threat - 1):
            return decode(fallback)

        defenses = _forced_captures(p, threat, 0)
        if not defenses:
            return decode(fallback)
        if len(defenses) == 1:
            return decode(defenses[0])

        fallback = engine.ordered(defenses, p, q, 0, qa, -1, 0)[0]
    else:
        safe_targets = _safe_penultimate(p, q, 0, qa)
        if safe_targets:
            for move in ordered:
                if (1 << (move & 63)) & safe_targets:
                    return decode(move)

    best_move = fallback
    previous_score = 0
    root_key = (p, q, 0)
    legal_set = set(legal)

    for depth in range(1, 65):
        if time.perf_counter() >= engine.deadline:
            break

        try:
            if depth >= 4 and abs(previous_score) < MATE_BOUND:
                alpha = previous_score - 75
                beta = previous_score + 75
            else:
                alpha, beta = -INF, INF

            score = engine.search(p, q, 0, depth, alpha, beta, 0)

            if score <= alpha or score >= beta:
                score = engine.search(p, q, 0, depth, -INF, INF, 0)

            entry = engine.tt.get(root_key)
            if entry is not None and entry[3] in legal_set:
                best_move = entry[3]

            previous_score = score
            if abs(score) > MATE_BOUND:
                break

        except _SearchTimeout:
            break

    # Only root moves produced by the legal move generator can be returned.
    if best_move not in legal_set:
        best_move = fallback
    return decode(best_move)

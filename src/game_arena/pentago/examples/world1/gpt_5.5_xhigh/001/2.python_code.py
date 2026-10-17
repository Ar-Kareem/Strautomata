
import time

BOARD_MASK = (1 << 36) - 1
BITS = tuple(1 << i for i in range(36))
RANGE8 = range(8)

WIN_SCORE = 1_000_000_000
TIME_LIMIT = 0.92

# Line weights for 5-cell windows with no enemy stones.
LINE_W = (0, 5, 35, 240, 5000, 10_000_000)


class _TimeUp(Exception):
    pass


def _build_win_masks():
    masks = set()
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for r in range(6):
        for c in range(6):
            for dr, dc in directions:
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        m |= 1 << ((r + k * dr) * 6 + (c + k * dc))
                    masks.add(m)
    return tuple(sorted(masks))


WIN_MASKS = _build_win_masks()


def _build_pos_data():
    # Quadrant centers and central cells are useful because they are stable or
    # participate in many potential lines.
    mat = (
        (3, 4, 4, 4, 4, 3),
        (4, 8, 5, 5, 8, 4),
        (4, 5, 7, 7, 5, 4),
        (4, 5, 7, 7, 5, 4),
        (4, 8, 5, 5, 8, 4),
        (3, 4, 4, 4, 4, 3),
    )
    weights = []
    groups = {}
    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            w = mat[r][c]
            weights.append(w)
            groups[w] = groups.get(w, 0) | BITS[idx]

    pos_groups = tuple((mask, w * 3) for w, mask in sorted(groups.items(), reverse=True))
    preferred = tuple(sorted(range(36), key=lambda i: (weights[i], -i), reverse=True))
    return tuple(weights), pos_groups, preferred


POS_WEIGHTS, POS_GROUPS, PREFERRED_CELLS = _build_pos_data()


def _build_rotations():
    out_masks = []
    pairs = []
    qd = []

    for q in range(4):
        r0 = 0 if q < 2 else 3
        c0 = 0 if (q % 2) == 0 else 3

        quadmask = 0
        cells = []
        for lr in range(3):
            for lc in range(3):
                src = (r0 + lr) * 6 + (c0 + lc)
                quadmask |= 1 << src
                cells.append((lr, lc, src))

        for d in ("L", "R"):
            ps = []
            for lr, lc, src in cells:
                if d == "R":
                    nr, nc = lc, 2 - lr
                else:
                    nr, nc = 2 - lc, lr
                dst = (r0 + nr) * 6 + (c0 + nc)
                ps.append((1 << src, 1 << dst))

            out_masks.append(BOARD_MASK ^ quadmask)
            pairs.append(tuple(ps))
            qd.append((q, d))

    return tuple(out_masks), tuple(pairs), tuple(qd)


ROT_OUT_MASKS, ROT_PAIRS, ROT_QD = _build_rotations()


def _build_move_strings():
    arr = []
    for cell in range(36):
        r, c = divmod(cell, 6)
        arr.append(tuple(f"{r + 1},{c + 1},{q},{d}" for q, d in ROT_QD))
    return tuple(arr)


MOVE_STRINGS = _build_move_strings()
CELL_QUADS = tuple((0 if (i // 6) < 3 else 2) + (1 if (i % 6) >= 3 else 0) for i in range(36))


def _build_stable_moves():
    # Fallback moves prefer rotating a different quadrant so the placed marble
    # remains where it was placed.
    res = []
    for cell in range(36):
        cq = CELL_QUADS[cell]
        chosen = 0
        for ridx, (q, _d) in enumerate(ROT_QD):
            if q != cq:
                chosen = ridx
                break
        res.append(MOVE_STRINGS[cell][chosen])
    return tuple(res)


STABLE_MOVES = _build_stable_moves()


def _to_bits(arr):
    b = 0
    for r in range(6):
        row = arr[r]
        base = r * 6
        for c in range(6):
            if row[c]:
                b |= 1 << (base + c)
    return b


def _rotate(bb, ridx):
    res = bb & ROT_OUT_MASKS[ridx]
    for src, dst in ROT_PAIRS[ridx]:
        if bb & src:
            res |= dst
    return res


def _has_win(bb, masks=WIN_MASKS):
    for m in masks:
        if (bb & m) == m:
            return True
    return False


def _terminal_for_mover(mover_after, other_after):
    mover_win = _has_win(mover_after)
    other_win = _has_win(other_after)

    if mover_win:
        return 0 if other_win else WIN_SCORE
    if other_win:
        return -WIN_SCORE
    if (mover_after | other_after) == BOARD_MASK:
        return 0
    return None


def _evaluate(me, opp):
    score = 0
    my4 = opp4 = my3 = opp3 = 0

    for m in WIN_MASKS:
        mb = me & m
        ob = opp & m

        if ob == 0:
            c = mb.bit_count()
            score += LINE_W[c]
            if c == 4:
                my4 += 1
            elif c == 3:
                my3 += 1
        elif mb == 0:
            c = ob.bit_count()
            score -= LINE_W[c]
            if c == 4:
                opp4 += 1
            elif c == 3:
                opp3 += 1

    # Side-to-move open fours are often immediate tactical wins; opponent
    # fours are urgent but usually blockable if singular.
    if my4:
        score += 120000 + 25000 * (my4 - 1)
    if opp4:
        score -= 45000 + 18000 * (opp4 - 1)

    if my3 > 1:
        score += 700 * (my3 - 1)
    if opp3 > 1:
        score -= 650 * (opp3 - 1)

    for pm, pw in POS_GROUPS:
        score += pw * ((me & pm).bit_count() - (opp & pm).bit_count())

    return score


def _fallback_bits(me, opp):
    empty = BOARD_MASK & ~(me | opp)
    for cell in PREFERRED_CELLS:
        if empty & BITS[cell]:
            return STABLE_MOVES[cell]
    if empty:
        cell = (empty & -empty).bit_length() - 1
        return STABLE_MOVES[cell]
    return "1,1,0,L"


def _opponent_reply_value(us, opp):
    # State is after our move; opponent is to move. Return value from our view.
    empty = BOARD_MASK & ~(us | opp)
    if not empty:
        return 0

    rot = _rotate
    term = _terminal_for_mover
    evalf = _evaluate
    rot_us = [rot(us, r) for r in RANGE8]

    worst = WIN_SCORE
    e = empty
    while e:
        bit = e & -e
        placed = opp | bit

        for ridx in RANGE8:
            opp_after = rot(placed, ridx)
            us_after = rot_us[ridx]
            tv = term(opp_after, us_after)

            if tv is None:
                v = evalf(us_after, opp_after)
            elif tv == WIN_SCORE:
                return -WIN_SCORE
            elif tv == -WIN_SCORE:
                v = WIN_SCORE
            else:
                v = 0

            if v < worst:
                worst = v

        e ^= bit

    return worst


def _winning_placement_count(me, opp, limit=4):
    # Counts distinct placement cells that have at least one winning rotation.
    empty = BOARD_MASK & ~(me | opp)
    if not empty:
        return 0

    rot = _rotate
    term = _terminal_for_mover
    rot_opp = [rot(opp, r) for r in RANGE8]

    count = 0
    e = empty
    while e:
        bit = e & -e
        placed = me | bit
        wins = False

        for ridx in RANGE8:
            if term(rot(placed, ridx), rot_opp[ridx]) == WIN_SCORE:
                wins = True
                break

        if wins:
            count += 1
            if count >= limit:
                return count

        e ^= bit

    return count


def _has_winning_move(me, opp, deadline=None):
    # Exact immediate-win test: a move must win without also giving a draw.
    empty = BOARD_MASK & ~(me | opp)
    if not empty:
        return False

    rot = _rotate
    term = _terminal_for_mover
    rot_opp = [rot(opp, r) for r in RANGE8]

    checked = 0
    e = empty
    while e:
        if deadline is not None and (checked & 3) == 0 and time.perf_counter() > deadline:
            raise _TimeUp()

        bit = e & -e
        placed = me | bit

        for ridx in RANGE8:
            if term(rot(placed, ridx), rot_opp[ridx]) == WIN_SCORE:
                return True

        checked += 1
        e ^= bit

    return False


def _forces_win_next(us, opp, deadline):
    # True if every legal opponent reply still lets us win immediately.
    empty = BOARD_MASK & ~(us | opp)
    if not empty:
        return False

    rot = _rotate
    term = _terminal_for_mover
    rot_us = [rot(us, r) for r in RANGE8]

    checked = 0
    e = empty
    while e:
        if (checked & 1) == 0 and time.perf_counter() > deadline:
            raise _TimeUp()

        bit = e & -e
        placed = opp | bit

        for ridx in RANGE8:
            opp_after = rot(placed, ridx)
            us_after = rot_us[ridx]
            tv = term(opp_after, us_after)

            if tv is None:
                if not _has_winning_move(us_after, opp_after, deadline):
                    return False
            elif tv == WIN_SCORE:
                return False
            elif tv == 0:
                return False
            else:
                # Opponent's reply immediately loses, so it is fine for us.
                pass

        checked += 1
        e ^= bit

    return True


def _policy_impl(you, opponent):
    start = time.perf_counter()

    me = _to_bits(you)
    opp = _to_bits(opponent)
    occ = me | opp
    empty = BOARD_MASK & ~occ

    fallback = _fallback_bits(me, opp)
    if not empty:
        return fallback

    # Strong and stable standard Pentago opening.
    if occ == 0:
        return "2,2,0,L"

    root = []
    draw_moves = []
    best_unsafe_score = -10**30
    best_unsafe_move = fallback

    rot = _rotate
    term = _terminal_for_mover
    evalf = _evaluate
    rot_opp = [rot(opp, r) for r in RANGE8]

    # Generate all legal root moves. Take an immediate non-draw win.
    e = empty
    while e:
        bit = e & -e
        cell = bit.bit_length() - 1
        placed = me | bit
        pos_bonus = POS_WEIGHTS[cell] * 4
        cell_moves = MOVE_STRINGS[cell]

        for ridx in RANGE8:
            me2 = rot(placed, ridx)
            opp2 = rot_opp[ridx]
            tv = term(me2, opp2)
            mstr = cell_moves[ridx]

            if tv is None:
                h = evalf(me2, opp2) + pos_bonus
                root.append((h, mstr, me2, opp2))
            elif tv == WIN_SCORE:
                return mstr
            elif tv == 0:
                draw_moves.append((POS_WEIGHTS[cell], mstr))
            else:
                score = -WIN_SCORE + pos_bonus
                if score > best_unsafe_score:
                    best_unsafe_score = score
                    best_unsafe_move = mstr

        e ^= bit

    if not root:
        if draw_moves:
            return max(draw_moves, key=lambda x: x[0])[1]
        return best_unsafe_move

    root.sort(key=lambda t: t[0], reverse=True)

    safe = []
    root_soft_deadline = start + 0.80

    # Full opponent-reply safety/minimax pass, with a soft time cutoff once we
    # already have at least one safe candidate.
    for idx, item in enumerate(root):
        if safe and idx > 12 and time.perf_counter() > root_soft_deadline:
            break

        h, mstr, me2, opp2 = item
        val = _opponent_reply_value(me2, opp2)

        if val <= -WIN_SCORE // 2:
            score = -WIN_SCORE + h // 1000
            if score > best_unsafe_score:
                best_unsafe_score = score
                best_unsafe_move = mstr
        else:
            safe.append((val, h, mstr, me2, opp2))

    if safe:
        safe.sort(key=lambda t: (t[0], t[1]), reverse=True)

        enriched = []
        threat_deadline = start + 0.86
        threat_limit = min(48, len(safe))

        for idx, (val, h, mstr, me2, opp2) in enumerate(safe):
            threats = 0
            if idx < threat_limit and time.perf_counter() < threat_deadline:
                threats = _winning_placement_count(me2, opp2, 4)

            combined = val + threats * 3000 + max(0, threats - 1) * 4000 + h // 2000
            enriched.append((combined, val, threats, h, mstr, me2, opp2))

        enriched.sort(key=lambda t: (t[0], t[1], t[2], t[3]), reverse=True)

        # If spare time remains, detect direct forced wins among top candidates.
        force_deadline = start + TIME_LIMIT
        if time.perf_counter() < force_deadline - 0.04:
            candidates = sorted(enriched[:min(12, len(enriched))], key=lambda t: (t[2], t[0]), reverse=True)
            checked = 0
            for cand in candidates:
                if time.perf_counter() > force_deadline - 0.025:
                    break
                if cand[2] == 0 and checked >= 4:
                    continue

                try:
                    if _forces_win_next(cand[5], cand[6], force_deadline):
                        return cand[4]
                except _TimeUp:
                    break

                checked += 1

        return enriched[0][4]

    if draw_moves:
        return max(draw_moves, key=lambda x: x[0])[1]

    return best_unsafe_move


def _array_fallback(you, opponent):
    for r in range(6):
        for c in range(6):
            try:
                if not you[r][c] and not opponent[r][c]:
                    return f"{r + 1},{c + 1},0,L"
            except Exception:
                pass
    return "1,1,0,L"


def policy(you, opponent) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        # Last-resort legality guard.
        return _array_fallback(you, opponent)
